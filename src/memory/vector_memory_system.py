# src/memory/vector_memory_system.py
import logging
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import text

from src.service.config import MemoryConfig, DatabaseConfig
from src.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class VectorMemorySystem:
    def __init__(self, memory_config: MemoryConfig, database_config: DatabaseConfig):
        self.memory_config = memory_config
        self.database_config = database_config
        self.db_connection = DatabaseConnection.from_config(database_config)

        self.collection_name = memory_config.collection_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=memory_config.embedding_model
        )
        self.sentence_model = SentenceTransformer(memory_config.embedding_model)
        self.vector_store = None

    async def initialize(self):
        if not await self.db_connection.test_connection():
            raise ConnectionError("Failed to connect to database")

        await self.db_connection.ensure_schema()

        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            **self.db_connection.get_pgvector_config(),
        )

        try:
            await self._ensure_vector_tables_exist()
            logger.info("✅ Vector tables ensured")
        except Exception as e:
            logger.warning(f"⚠️ Vector table init skipped: {e}")

    async def _ensure_vector_tables_exist(self):
        try:
            await self.vector_store.aadd_texts(
                ["hello world"], ids=["init"], metadata=[{"__init": "true"}]
            )
            await self.vector_store.adelete(["init"])
            logger.debug("✅ Vector tables created and verified")
        except Exception as e:
            logger.warning(f"⚠️ Vector table init skipped: {e}")

    async def add_memory(
        self,
        thread_id: str,
        content: str,
        memory_type="observation",
        importance_score=0.5,
        emotional_tone="neutral",
        topics=None,
        metadata=None,
    ):
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

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        results = await self.vector_store.asimilarity_search(query, k=k)
        if thread_id:
            results = [
                doc for doc in results if doc.metadata.get("thread_id") == thread_id
            ]
        return results[:k]

    async def get_memory_stats(self) -> Dict[str, Any]:
        stats = {
            "total_memories": 0,
            "total_conversations": 0,
            "backend": "pgvector",
            "status": "not_initialized",
            "embedding_model": self.memory_config.embedding_model,
            "vector_dimensions": self.memory_config.embedding_dimension,
        }

        session = await self.db_connection.get_session()
        async with session:
            try:
                result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM langchain_pg_embedding 
                        WHERE collection_id = CAST(
                            (SELECT id FROM langchain_pg_collection WHERE name = :name)
                            AS UUID
                        )
                    """
                    ),
                    {"name": self.collection_name},
                )
                stats["total_memories"] = result.scalar_one()
                stats["status"] = "active"
            except Exception as e:
                stats["status"] = "error"
                stats["error"] = str(e)

        return stats

    async def close(self):
        await self.db_connection.close()
