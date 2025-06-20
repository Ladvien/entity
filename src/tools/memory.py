# entity_service/memory.py
"""
Vector Memory System using PostgreSQL
(Keep your existing implementation with minor adjustments)
"""
from typing import List, Optional, Dict, Any
import logging

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_postgres.vectorstores import PGVector

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

from pydantic import BaseModel

from src.service.config import DatabaseConfig, MemoryConfig

logger = logging.getLogger(__name__)


class MemorySearchInput(BaseModel):
    query: str
    thread_id: str


class VectorMemorySystem:
    """
    Vector memory system using LangChain's PGVector.
    Stores conversational and observational memory with metadata.
    """

    def __init__(self, memory_config: MemoryConfig, database_config: DatabaseConfig):
        self.memory_config = memory_config
        self.database_config = database_config

        self.collection_name = memory_config.collection_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=memory_config.embedding_model
        )
        self.sentence_model = SentenceTransformer(memory_config.embedding_model)
        self.vector_store = None
        self.engine: Optional[AsyncEngine] = None

    async def initialize(self):
        """Initialize the vector store"""
        conn_url = (
            f"postgresql+asyncpg://{self.database_config.username}:"
            f"{self.database_config.password}"
            f"@{self.database_config.host}:"
            f"{self.database_config.port}/"
            f"{self.database_config.name}"
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

        logger.info("✅ PGVector memory initialized")

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
        """Add a memory entry"""
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
            logger.info("📝 Memory added to PGVector")
        except Exception:
            logger.exception("❌ Failed to add memory")

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        """Search memories"""
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
        """Get formatted memory context"""
        try:
            memories = await self.search_memory(query=query, thread_id=thread_id, k=k)
            if not memories:
                return ""

            context_parts = []
            for doc in memories:
                # Extract key info from metadata
                memory_type = doc.metadata.get("memory_type", "unknown")
                importance = doc.metadata.get("importance_score", 0.5)

                if importance > 0.7:
                    context_parts.append(f"[Important] {doc.page_content}")
                else:
                    context_parts.append(f"[{memory_type}] {doc.page_content}")

            return "\n".join(context_parts)
        except Exception:
            logger.exception("❌ Failed to retrieve memory context")
            return ""

    async def store_conversation(
        self, user_input: str, ai_response: str, thread_id: str = "default"
    ):
        """Store a conversation exchange"""
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
        """Get memory statistics"""
        stats = {
            "total_memories": 0,
            "total_conversations": 0,
            "memory_types": {},
            "emotions": {},
            "top_topics": {},
            "backend": "pgvector",
            "vector_dimensions": self.memory_config.embedding_dimension,
            "embedding_model": self.memory_config.embedding_model,
        }

        if not self.engine:
            logger.error("❌ Memory system not initialized")
            return stats

        try:
            async with self.engine.connect() as conn:
                # Get total count
                result = await conn.execute(
                    text(
                        """
                        SELECT COUNT(*) 
                        FROM langchain_pg_embedding 
                        WHERE collection_id = CAST(
                            (SELECT id FROM langchain_pg_collection WHERE name = :name) 
                            AS UUID
                        )
                        """
                    ),
                    {"name": self.collection_name},
                )

                stats["total_memories"] = result.scalar_one()

                # Get metadata stats
                result = await conn.execute(
                    text(
                        """
                        SELECT cmetadata 
                        FROM langchain_pg_embedding 
                        WHERE collection_id = CAST(
                            (SELECT id FROM langchain_pg_collection WHERE name = :name)
                            AS UUID
                        )
                        LIMIT 1000
                        """
                    ),
                    {"name": self.collection_name},
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
                stats["top_topics"] = dict(
                    sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
                )

        except Exception:
            logger.exception("❌ Failed to get memory stats")

        return stats

    async def close(self):
        """Close connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Memory system closed")
