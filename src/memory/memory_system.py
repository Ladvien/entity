import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import text

from src.shared.models import ChatInteraction
from src.service.config import MemoryConfig, DatabaseConfig, StorageConfig
from src.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MemorySystem:
    def __init__(
        self,
        memory_config: MemoryConfig,
        database_config: DatabaseConfig,
        storage_config: StorageConfig,
    ):
        self.memory_config = memory_config
        self.database_config = database_config
        self.storage_config = storage_config
        self.history_table = storage_config.history_table

        self.db_connection = DatabaseConnection.from_config(database_config)
        self.collection_name = memory_config.collection_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=memory_config.embedding_model
        )
        self.vector_store = None

    async def initialize(self):
        await self.db_connection.ensure_schema()
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            **self.db_connection.get_pgvector_config(),
        )
        await self._ensure_history_table()
        await self._ensure_vector_collection()

    async def _ensure_history_table(self):
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.history_table} (
                id SERIAL PRIMARY KEY,
                interaction_id TEXT UNIQUE NOT NULL,
                thread_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                raw_input TEXT NOT NULL,
                raw_output TEXT NOT NULL,
                response TEXT NOT NULL,
                tools_used JSONB DEFAULT '[]',
                memory_context_used BOOLEAN DEFAULT FALSE,
                memory_context TEXT DEFAULT '',
                use_tools BOOLEAN DEFAULT TRUE,
                use_memory BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                response_time_ms FLOAT,
                token_count INTEGER,
                conversation_turn INTEGER,
                user_id TEXT,
                agent_personality_applied BOOLEAN DEFAULT FALSE,
                personality_adjustments JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{{}}'::jsonb
            )
        """
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{self.history_table}_thread_timestamp ON {self.history_table}(thread_id, timestamp DESC)"
        ]
        await self.db_connection.execute_schema_commands([create_sql] + indexes)

    async def _ensure_vector_collection(self):
        try:
            await self.vector_store.aadd_texts(
                ["init"], ids=["__init__"], metadata=[{"init": True}]
            )
            await self.vector_store.adelete(["__init__"])
        except Exception as e:
            logger.warning(f"⚠️ Vector collection init skipped: {e}")

    async def save_interaction(self, interaction: ChatInteraction):
        session = await self.db_connection.get_session()
        async with session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.history_table} (
                        interaction_id, thread_id, timestamp, raw_input, raw_output, response,
                        tools_used, memory_context_used, memory_context, use_tools, use_memory,
                        error_message, response_time_ms, token_count, conversation_turn, user_id,
                        agent_personality_applied, personality_adjustments, metadata
                    ) VALUES (
                        :interaction_id, :thread_id, :timestamp, :raw_input, :raw_output, :response,
                        :tools_used, :memory_context_used, :memory_context, :use_tools, :use_memory,
                        :error_message, :response_time_ms, :token_count, :conversation_turn, :user_id,
                        :agent_personality_applied, :personality_adjustments, :metadata
                    )
                    ON CONFLICT (interaction_id) DO NOTHING
                """
                ),
                {
                    "interaction_id": interaction.interaction_id,
                    "thread_id": interaction.thread_id,
                    "timestamp": interaction.timestamp,
                    "raw_input": interaction.raw_input,
                    "raw_output": interaction.raw_output,
                    "response": interaction.response,
                    "tools_used": json.dumps(interaction.tools_used),
                    "memory_context_used": interaction.memory_context_used,
                    "memory_context": interaction.memory_context,
                    "use_tools": interaction.use_tools,
                    "use_memory": interaction.use_memory,
                    "error_message": interaction.error,
                    "response_time_ms": interaction.response_time_ms,
                    "token_count": interaction.token_count,
                    "conversation_turn": interaction.conversation_turn,
                    "user_id": interaction.user_id,
                    "agent_personality_applied": interaction.agent_personality_applied,
                    "personality_adjustments": json.dumps(
                        interaction.personality_adjustments
                    ),
                    "metadata": json.dumps(interaction.metadata),
                },
            )

            if interaction.use_memory:
                doc = Document(
                    page_content=interaction.response,
                    metadata={
                        "interaction_id": interaction.interaction_id,
                        "thread_id": interaction.thread_id,
                        "timestamp": interaction.timestamp.isoformat(),
                        "tools_used": interaction.tools_used,
                        "user_id": interaction.user_id or "anonymous",
                    },
                )
                try:
                    await self.vector_store.aadd_documents([doc])
                except Exception as e:
                    logger.warning(f"⚠️ Could not store embedding for interaction: {e}")

            await session.commit()

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        results = await self.vector_store.asimilarity_search(query, k=k)
        if thread_id:
            results = [
                doc for doc in results if doc.metadata.get("thread_id") == thread_id
            ]
        return results[:k]

    async def deep_search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[ChatInteraction]:
        session = await self.db_connection.get_session()
        async with session:
            result = await session.execute(
                text(
                    f"""
                    SELECT * FROM {self.history_table}
                    WHERE (:thread_id IS NULL OR thread_id = :thread_id)
                    AND (
                        raw_input ILIKE :query OR
                        raw_output ILIKE :query OR
                        response ILIKE :query
                    )
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """
                ),
                {
                    "query": f"%{query}%",
                    "thread_id": thread_id,
                    "limit": k,
                },
            )
            rows = result.fetchall()

        return [
            ChatInteraction(
                interaction_id=row.interaction_id,
                thread_id=row.thread_id,
                timestamp=row.timestamp,
                raw_input=row.raw_input,
                raw_output=row.raw_output,
                response=row.response,
                tools_used=json.loads(row.tools_used or "[]"),
                memory_context_used=row.memory_context_used,
                memory_context=row.memory_context,
                use_tools=row.use_tools,
                use_memory=row.use_memory,
                error=row.error_message,
                response_time_ms=row.response_time_ms,
                token_count=row.token_count,
                conversation_turn=row.conversation_turn,
                user_id=row.user_id,
                agent_personality_applied=row.agent_personality_applied,
                personality_adjustments=json.loads(row.personality_adjustments or "[]"),
                metadata=json.loads(row.metadata or "{}"),
            )
            for row in rows
        ]

    async def get_history(
        self, thread_id: str, limit: int = 100
    ) -> List[ChatInteraction]:
        session = await self.db_connection.get_session()
        async with session:
            result = await session.execute(
                text(
                    f"""
                    SELECT * FROM {self.history_table}
                    WHERE thread_id = :thread_id
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """
                ),
                {"thread_id": thread_id, "limit": limit},
            )
            rows = result.fetchall()

        return [
            ChatInteraction(
                interaction_id=row.interaction_id,
                thread_id=row.thread_id,
                timestamp=row.timestamp,
                raw_input=row.raw_input,
                raw_output=row.raw_output,
                response=row.response,
                tools_used=json.loads(row.tools_used or "[]"),
                memory_context_used=row.memory_context_used,
                memory_context=row.memory_context,
                use_tools=row.use_tools,
                use_memory=row.use_memory,
                error=row.error_message,
                response_time_ms=row.response_time_ms,
                token_count=row.token_count,
                conversation_turn=row.conversation_turn,
                user_id=row.user_id,
                agent_personality_applied=row.agent_personality_applied,
                personality_adjustments=json.loads(row.personality_adjustments or "[]"),
                metadata=json.loads(row.metadata or "{}"),
            )
            for row in rows
        ]

    async def get_memory_stats(self) -> Dict[str, Any]:
        stats = {
            "total_memories": 0,
            "total_conversations": 0,
            "embedding_model": self.memory_config.embedding_model,
            "vector_dimensions": self.memory_config.embedding_dimension,
            "backend": "pgvector",
        }
        session = await self.db_connection.get_session()
        async with session:
            try:
                result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM langchain_pg_embedding 
                        WHERE collection_id = CAST((SELECT id FROM langchain_pg_collection WHERE name = :name) AS UUID)
                    """
                    ),
                    {"name": self.collection_name},
                )
                stats["total_memories"] = result.scalar_one()

                result = await session.execute(
                    text(f"SELECT COUNT(DISTINCT thread_id) FROM {self.history_table}")
                )
                stats["total_conversations"] = result.scalar_one()

            except Exception as e:
                stats["status"] = "error"
                stats["error"] = str(e)

        return stats

    async def close(self):
        await self.db_connection.close()
