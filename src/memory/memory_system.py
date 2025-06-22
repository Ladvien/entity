# src/memory/memory_system.py
import json
import logging
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sqlalchemy import text

from src.shared.models import ChatInteraction
from src.service.config import MemoryConfig, DatabaseConfig, StorageConfig
from src.db.connection import DatabaseConnection
from src.memory.custom_pgvector import SchemaAwarePGVector, SchemaAwarePGVectorNoDDL

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

        if not database_config.db_schema:
            raise ValueError("MemoryConfig must specify a schema name for PGVector")
        else:
            self.schema = database_config.db_schema

        self.db_connection = DatabaseConnection.from_config(database_config)
        self.collection_name = memory_config.collection_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=memory_config.embedding_model
        )
        self.vector_store = None

    def create_tables_if_not_exists(self):
        # Override to skip DDL at runtime to avoid greenlet errors
        pass

    async def initialize(self):
        await self.db_connection.ensure_schema()
        await self._ensure_pgvector_extension()
        await self._initialize_vector_store()
        await self._ensure_history_table()

    async def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is enabled"""
        try:
            session = await self.db_connection.get_session()
            async with session:
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("✅ pgvector extension enabled")
                await session.commit()

        except Exception as e:
            logger.error(f"❌ Failed to ensure pgvector extension: {e}")
            raise

    async def _initialize_vector_store(self):
        """Initialize vector store using our custom schema-aware PGVector - FIXED VERSION"""
        try:
            # Get the pgvector config
            pgvector_config = self.db_connection.get_pgvector_config()

            logger.info(
                f"🎯 Initializing SchemaAwarePGVector for schema: {self.schema}"
            )
            for key, value in pgvector_config.items():
                if "password" not in key.lower():
                    logger.info(f"     {key}: {value}")

            # Get the async engine once
            engine = await self.db_connection.get_engine()

            logger.info(f"Engine type before passing: {type(engine)}")

            self.vector_store = await SchemaAwarePGVectorNoDDL.afrom_texts(
                texts=[],
                embedding=self.embeddings,
                collection_name=self.collection_name,
                schema_name=self.schema,
                connection=engine,
                async_mode=pgvector_config.get("async_mode", True),
                create_extension=pgvector_config.get("create_extension", False),
                use_jsonb=pgvector_config.get("use_jsonb", True),
                pre_delete_collection=pgvector_config.get(
                    "pre_delete_collection", False
                ),
            )

            logger.info(f"✅ SchemaAwarePGVector created for schema: {self.schema}")

            # Verify the setup worked
            await self._verify_vector_setup()

        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise

    async def _verify_vector_setup(self):
        """Verify that vector store is properly set up in correct schema"""
        try:
            # Use the verification method from our custom PGVector
            if hasattr(self.vector_store, "_verify_schema_setup"):
                success = await self.vector_store._verify_schema_setup()
                if success:
                    logger.info(
                        f"🎉 Vector store successfully verified in {self.schema} schema"
                    )
                else:
                    logger.error(
                        f"💥 Vector store verification failed for {self.schema} schema"
                    )

            # Also log final table locations
            await self._log_final_table_locations()

        except Exception as e:
            logger.warning(f"⚠️ Vector setup verification failed: {e}")

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
        logger.info(
            f"✅ History table {self.history_table} ensured in {self.schema} schema"
        )

    async def _log_final_table_locations(self):
        """Log where all tables ended up"""
        try:
            session = await self.db_connection.get_session()
            async with session:
                result = await session.execute(
                    text(
                        """
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE tablename LIKE 'langchain_pg_%' OR tablename = :history_table
                    ORDER BY schemaname, tablename
                """
                    ),
                    {"history_table": self.history_table},
                )

                tables = result.fetchall()
                logger.info("📍 FINAL table locations with custom PGVector:")
                for schema, table in tables:
                    if schema == self.schema:
                        logger.info(f"  ✅ {schema}.{table} (CORRECT SCHEMA)")
                    else:
                        logger.warning(f"  ❌ {schema}.{table} (WRONG SCHEMA)")

                # Count tables in target schema
                target_count = sum(
                    1
                    for schema, table in tables
                    if schema == self.schema and "langchain_pg" in table
                )
                public_count = sum(
                    1
                    for schema, table in tables
                    if schema == "public" and "langchain_pg" in table
                )

                if target_count >= 2 and public_count == 0:
                    logger.info(
                        f"🎉 SUCCESS: All vector tables in {self.schema} schema!"
                    )
                elif target_count >= 2:
                    logger.warning(
                        f"⚠️ Vector tables in {self.schema} schema, but duplicates in public"
                    )
                else:
                    logger.error(
                        f"💥 FAILURE: Vector tables not in {self.schema} schema"
                    )

        except Exception as e:
            logger.warning(f"Could not log table locations: {e}")

    async def save_interaction(self, interaction: ChatInteraction):
        logger.info(f"Saving interaction: {interaction.interaction_id}")
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

            if interaction.use_memory and self.vector_store:
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
                    logger.debug(
                        f"📝 Adding vector embedding for interaction {interaction.interaction_id}"
                    )
                    await self.vector_store.aadd_documents([doc])
                    logger.debug(f"✅ Added vector embedding to {self.schema} schema")
                except Exception as e:
                    logger.warning(f"⚠️ Could not store embedding for interaction: {e}")

            await session.commit()

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return []

        try:
            logger.debug(
                f"🔍 Searching vector memory for: '{query}' (thread: {thread_id})"
            )
            results = await self.vector_store.asimilarity_search(query, k=k)

            if thread_id:
                results = [
                    doc for doc in results if doc.metadata.get("thread_id") == thread_id
                ]

            logger.debug(f"🔍 Found {len(results)} vector results")
            return results[:k]
        except Exception as e:
            logger.warning(f"⚠️ Vector search failed: {e}")
            return []

    async def deep_search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[ChatInteraction]:
        session = await self.db_connection.get_session()
        async with session:
            if thread_id:
                sql_query = f"""
                    SELECT * FROM {self.history_table}
                    WHERE thread_id = :thread_id
                    AND (
                        raw_input ILIKE :query OR
                        raw_output ILIKE :query OR
                        response ILIKE :query
                    )
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """
                params = {
                    "thread_id": thread_id,
                    "query": f"%{query}%",
                    "limit": k,
                }
            else:
                sql_query = f"""
                    SELECT * FROM {self.history_table}
                    WHERE (
                        raw_input ILIKE :query OR
                        raw_output ILIKE :query OR
                        response ILIKE :query
                    )
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """
                params = {
                    "query": f"%{query}%",
                    "limit": k,
                }

            result = await session.execute(text(sql_query), params)
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
            "schema": self.schema,
        }
        session = await self.db_connection.get_session()
        async with session:
            try:
                # Check vector embeddings in our target schema
                result = await session.execute(
                    text(
                        f"""
                        SELECT COUNT(*) FROM "{self.schema}".langchain_pg_embedding 
                        WHERE collection_id = CAST((
                            SELECT uuid FROM "{self.schema}".langchain_pg_collection 
                            WHERE name = :name
                        ) AS UUID)
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
                logger.warning(f"Error getting memory stats: {e}")
                stats["status"] = "error"
                stats["error"] = str(e)

        return stats

    async def close(self):
        await self.db_connection.close()
