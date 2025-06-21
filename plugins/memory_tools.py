# plugins/memory_tools.py

import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_postgres.vectorstores import PGVector

from sqlalchemy import text

from src.core.registry import ServiceRegistry
from src.service.config import MemoryConfig, DatabaseConfig
from src.db.connection import DatabaseConnection
from src.tools.base_tools import BaseToolPlugin

logger = logging.getLogger(__name__)


# --- Vector Memory System --- #


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

        conn_url = self.db_connection.get_async_connection_url()
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            connection=conn_url,
            collection_name=self.collection_name,
            create_extension=False,
            async_mode=True,
            use_jsonb=True,
        )

        try:
            await self._ensure_vector_tables_exist()
            logger.info("✅ Vector tables ensured")
        except Exception as e:
            logger.warning(f"⚠️ Vector table init skipped: {e}")

    async def _ensure_vector_tables_exist(self):
        dummy_doc = Document(
            page_content="__INIT_DUMMY__",
            metadata={"__init": True, "thread_id": "__init__"},
        )
        await self.vector_store.aadd_documents([dummy_doc])

        session = await self.db_connection.get_session()
        async with session:
            await session.execute(
                text(
                    """
                    DELETE FROM langchain_pg_embedding 
                    WHERE collection_id = CAST(
                        (SELECT id FROM langchain_pg_collection WHERE name = :name) 
                        AS UUID
                    ) AND cmetadata->>'__init' = 'true'
                """
                ),
                {"name": self.collection_name},
            )
            await session.commit()

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


# --- Tool Interfaces --- #


class MemorySearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    thread_id: Optional[str] = Field(default="default")
    limit: Optional[int] = Field(default=5)


class StoreMemoryInput(BaseModel):
    content: str = Field(..., description="Memory content")
    thread_id: Optional[str] = Field(default="default")
    memory_type: Optional[str] = Field(default="observation")
    importance_score: Optional[float] = Field(default=0.5)


# --- Tools --- #


class MemorySearchTool(BaseToolPlugin):
    name = "memory_search"
    description = "Search stored memories"
    args_schema = MemorySearchInput

    async def run(self, input_data: MemorySearchInput) -> str:
        memory = ServiceRegistry.try_get("memory_system")
        if not memory:
            return "❌ Memory system not available"

        results = await memory.search_memory(
            query=input_data.query,
            thread_id=input_data.thread_id,
            k=input_data.limit,
        )

        if not results:
            return f"No memories found for: {input_data.query}"

        return "\n".join(
            f"{i+1}. [{doc.metadata.get('memory_type', 'unknown')}] {doc.page_content[:80]}..."
            for i, doc in enumerate(results)
        )


class StoreMemoryTool(BaseToolPlugin):
    name = "store_memory"
    description = "Store a memory entry"
    args_schema = StoreMemoryInput

    async def run(self, input_data: StoreMemoryInput) -> str:
        memory = ServiceRegistry.try_get("memory_system")
        if not memory:
            return "❌ Memory system not available"

        await memory.add_memory(
            thread_id=input_data.thread_id,
            content=input_data.content,
            memory_type=input_data.memory_type,
            importance_score=input_data.importance_score,
        )

        return "✅ Memory stored successfully"


# --- Aliases --- #


class SearchMemoriesTool(MemorySearchTool):
    name = "search_memories"
    description = "Alias for memory_search"


class MemoryStoreTool(StoreMemoryTool):
    name = "memory_store"
    description = "Alias for store_memory"
