from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_postgres import PGEngine, Column
from langchain_postgres import PGVectorStore
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
import logging

from src.config import MemoryConfig

logger = logging.getLogger(__name__)


class VectorMemorySystem:
    """
    Simplified vector memory system using LangChain's PGVectorStore.
    Enriched metadata supported for emotional tone, importance, topics, etc.
    """

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.collection_name = self.config.memory.collection_name
        self.vector_store = None
        self.model_name = self.config.memory.embedding_model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.memory.embedding_model
        )
        self.sentence_model = SentenceTransformer(self.config.memory.embedding_model)
        self.pg_engine = None

    async def initialize(self):
        try:
            conn_url = (
                f"postgresql+asyncpg://{self.config.database.username}:{self.config.database.password}"
                f"@{self.config.database.host}:{self.config.database.port}/{self.config.database.name}"
            )

            self.pg_engine = PGEngine.from_connection_string(url=conn_url)
            vector_dim = self.sentence_model.get_sentence_embedding_dimension()

            await self.pg_engine.ainit_vectorstore_table(
                table_name=self.collection_name,
                vector_size=vector_dim,
                metadata_columns=[
                    Column("thread_id", "TEXT"),
                    Column("memory_type", "TEXT"),
                    Column("importance_score", "FLOAT"),
                    Column("emotional_tone", "TEXT"),
                    Column("topics", "JSONB"),
                ],
            )

            self.vector_store = await PGVectorStore.create(
                engine=self.pg_engine,
                table_name=self.collection_name,
                embedding=self.embeddings,
                metadata_columns=[
                    "thread_id",
                    "memory_type",
                    "importance_score",
                    "emotional_tone",
                    "topics",
                ],
            )

            logger.info("✅ PGVectorStore memory initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize PGVectorStore: {e}")
            raise

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
        except Exception as e:
            logger.error(f"❌ Failed to add memory: {e}")

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
        except Exception as e:
            logger.error(f"❌ Memory search failed: {e}")
            return []
