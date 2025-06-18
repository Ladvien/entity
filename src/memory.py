from typing import List, Optional, Dict, Any
import logging

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_postgres.vectorstores import PGVector

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

from src.config import MemoryConfig

logger = logging.getLogger(__name__)


class VectorMemorySystem:
    """
    Vector memory system using LangChain's PGVector.
    Stores conversational and observational memory with metadata.
    """

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.collection_name = config.collection_name
        self.embeddings = HuggingFaceEmbeddings(model_name=config.embedding_model)
        self.sentence_model = SentenceTransformer(config.embedding_model)
        self.vector_store = None
        self.engine: Optional[AsyncEngine] = None

    async def initialize(self):
        conn_url = (
            f"postgresql+asyncpg://{self.config.database.username}:"
            f"{self.config.database.password}"
            f"@{self.config.database.host}:"
            f"{self.config.database.port}/"
            f"{self.config.database.name}"
        )

        self.engine = create_async_engine(conn_url, echo=False)

        self.vector_store = PGVector(
            embeddings=self.embeddings,
            connection=conn_url,
            collection_name=self.collection_name,
            create_extension=False,
            async_mode=True,
            use_jsonb=True,
        )

        logger.info("✅ PGVectorStore memory initialized")

    async def add_memory(
        self,
        thread_id: str,
        content: str,
        memory_type: str = "observation",
        importance_score: float = 0.5,
        emotional_tone: str = "neutral",
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        try:
            doc = Document(
                page_content=content,
                metadata={
                    "thread_id": thread_id,
                    "memory_type": memory_type,
                    "importance_score": importance_score,
                    "emotional_tone": emotional_tone,
                    "topics": topics or [],
                    **(metadata or {}),
                },
            )
            await self.vector_store.aadd_documents([doc])
            logger.info("📝 Memory added to PGVectorStore")
        except Exception:
            logger.exception("❌ Failed to add memory")

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        try:
            filter_ = {"thread_id": {"$eq": thread_id}} if thread_id else None
            results = await self.vector_store.asimilarity_search(
                query, k=k, filter=filter_
            )
            logger.info(f"🔍 Retrieved {len(results)} memory entries")
            return results
        except Exception:
            logger.exception("❌ Memory search failed")
            return []

    async def get_memory_context(
        self, query: str, thread_id: str = "default", k: int = 5
    ) -> str:
        try:
            memories = await self.search_memory(query=query, thread_id=thread_id, k=k)
            return "\n".join([f"- {doc.page_content}" for doc in memories])
        except Exception:
            logger.exception("❌ Failed to retrieve memory context")
            return ""

    async def store_conversation(
        self, user_input: str, ai_response: str, thread_id: str = "default"
    ):
        try:
            combined_text = f"User: {user_input}\nAssistant: {ai_response}"
            await self.add_memory(
                thread_id=thread_id,
                content=combined_text,
                memory_type="conversation",
                importance_score=0.5,
                emotional_tone="neutral",
            )
            logger.info("💾 Conversation stored in vector memory")
        except Exception:
            logger.exception("❌ Failed to store conversation")

    async def get_memory_stats(self) -> Dict[str, Any]:
        stats = {
            "total_memories": -1,
            "total_conversations": 0,
            "memory_types": {},
            "emotions": {},
            "top_topics": {},
            "backend": "pgvector",
        }

        if not self.engine:
            logger.error("❌ Memory system not initialized (no engine)")
            return stats

        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM langchain_pg_embedding")
                )
                stats["total_memories"] = result.scalar_one()

                result = await conn.execute(
                    text("SELECT cmetadata FROM langchain_pg_embedding LIMIT 1000")
                )
                rows = result.fetchall()

                thread_ids = set()
                memory_types = {}
                emotions = {}
                topics = {}

                for row in rows:
                    meta = row[0] or {}
                    thread_ids.add(meta.get("thread_id", "default"))
                    mt = meta.get("memory_type", "observation")
                    memory_types[mt] = memory_types.get(mt, 0) + 1
                    tone = meta.get("emotional_tone", "neutral")
                    emotions[tone] = emotions.get(tone, 0) + 1
                    for topic in meta.get("topics", []):
                        topics[topic] = topics.get(topic, 0) + 1

                stats["total_conversations"] = len(thread_ids)
                stats["memory_types"] = memory_types
                stats["emotions"] = emotions
                stats["top_topics"] = topics

        except Exception:
            logger.exception("❌ Failed to get memory stats")

        return stats

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ PGVectorStore memory engine closed")
