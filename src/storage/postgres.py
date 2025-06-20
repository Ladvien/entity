# src/storage/postgres.py - Fix connection URL

import json
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any
import logging
from datetime import datetime

from src.service.config import DatabaseConfig, StorageConfig
from src.storage.base import BaseChatStorage
from src.shared.models import ChatInteraction

logger = logging.getLogger(__name__)


class PostgresChatStorage(BaseChatStorage):
    def __init__(self, db_config: DatabaseConfig, storage_config: StorageConfig):
        self.db_config = db_config
        self.storage_config = storage_config

        # Get schema, ensuring it's a string
        schema = str(getattr(db_config, "schema", "public"))

        # Basic connection URL without options
        self.conn_url = (
            f"postgresql+asyncpg://{db_config.username}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.name}"
        )

        # Create engine with schema in connect_args - ensure all values are strings
        connect_args = {}
        if schema and schema != "public":
            connect_args["server_settings"] = {"search_path": schema}

        self.engine = create_async_engine(
            self.conn_url, echo=False, connect_args=connect_args
        )

        self.session_factory = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def initialize(self):
        if not self.storage_config.init_on_startup:
            return

        schema = getattr(self.db_config, "schema", "public")

        try:
            async with self.engine.begin() as conn:
                # Create schema if it doesn't exist (skip for public schema)
                if schema != "public":
                    await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                    logger.info(f"✅ Schema '{schema}' ready")

                # Set search path for this session
                await conn.execute(text(f"SET search_path TO {schema}"))

                # Create table with enhanced structure
                await conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self.storage_config.history_table} (
                            id SERIAL PRIMARY KEY,
                            thread_id TEXT NOT NULL,
                            timestamp TIMESTAMP NOT NULL,
                            
                            -- Core interaction data
                            response TEXT NOT NULL,
                            raw_input TEXT NOT NULL,
                            raw_output TEXT NOT NULL,
                            
                            -- Tool and memory usage
                            tools_used JSONB DEFAULT '[]'::jsonb,
                            memory_context_used BOOLEAN DEFAULT FALSE,
                            
                            -- Settings and metadata
                            use_tools BOOLEAN DEFAULT TRUE,
                            use_memory BOOLEAN DEFAULT TRUE,
                            error_message TEXT,
                            
                            -- Additional metadata (for extensibility)
                            metadata JSONB DEFAULT '{{}}'::jsonb,
                            
                            -- Indexes for common queries
                            CONSTRAINT valid_thread_id CHECK (length(thread_id) > 0)
                        );
                        
                        -- Create indexes for performance
                        CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_thread_id 
                            ON {self.storage_config.history_table}(thread_id);
                        CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_timestamp 
                            ON {self.storage_config.history_table}(timestamp DESC);
                        CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_thread_timestamp 
                            ON {self.storage_config.history_table}(thread_id, timestamp DESC);
                        """
                    )
                )
                logger.info(
                    f"✅ Table '{schema}.{self.storage_config.history_table}' ready"
                )

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    async def save_interaction(self, interaction: ChatInteraction):
        """Save a ChatInteraction to the database"""
        try:
            async with self.session_factory() as session:
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.storage_config.history_table}
                        (thread_id, timestamp, response, raw_input, raw_output, 
                         tools_used, memory_context_used, use_tools, use_memory, error_message, metadata)
                        VALUES (:thread_id, :timestamp, :response, :raw_input, :raw_output,
                               :tools_used, :memory_context_used, :use_tools, :use_memory, :error_message, :metadata)
                        """
                    ),
                    {
                        "thread_id": interaction.thread_id,
                        "timestamp": interaction.timestamp,
                        "response": interaction.response,
                        "raw_input": interaction.raw_input,
                        "raw_output": interaction.raw_output,
                        "tools_used": json.dumps(interaction.tools_used),
                        "memory_context_used": interaction.memory_context_used,
                        "use_tools": interaction.use_tools,
                        "use_memory": interaction.use_memory,
                        "error_message": interaction.error,
                        "metadata": json.dumps({}),  # For future extensibility
                    },
                )
                await session.commit()
            logger.debug("💾 Chat interaction saved")
        except Exception:
            logger.exception("❌ Failed to store chat interaction")

    # Legacy method for backward compatibility
    async def save_interaction_legacy(
        self,
        thread_id: str,
        user_input: str,
        agent_output: str,
        metadata: Dict[str, Any],
    ):
        """Legacy save method - converts to ChatInteraction and saves"""
        interaction = ChatInteraction(
            response=agent_output,
            thread_id=thread_id,
            timestamp=metadata.get("timestamp", datetime.utcnow()),
            raw_input=user_input,
            raw_output=metadata.get("raw_output", agent_output),
            tools_used=metadata.get("tools_used", []),
            memory_context_used=metadata.get("had_memory_context", False),
            use_tools=metadata.get("use_tools", True),
            use_memory=metadata.get("use_memory", True),
            error=metadata.get("error"),
        )
        await self.save_interaction(interaction)

    async def get_history(
        self, thread_id: str, limit: int = 100
    ) -> List[ChatInteraction]:
        """Get chat history as list of ChatInteraction objects"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        f"""
                        SELECT thread_id, timestamp, response, raw_input, raw_output,
                               tools_used, memory_context_used, use_tools, use_memory, 
                               error_message, metadata
                        FROM {self.storage_config.history_table}
                        WHERE thread_id = :thread_id
                        ORDER BY timestamp DESC
                        LIMIT :limit
                        """
                    ),
                    {"thread_id": thread_id, "limit": limit},
                )
                rows = result.fetchall()

                interactions = []
                for row in rows:
                    interaction = ChatInteraction(
                        response=row.response,
                        thread_id=row.thread_id,
                        timestamp=row.timestamp,
                        raw_input=row.raw_input,
                        raw_output=row.raw_output,
                        tools_used=json.loads(row.tools_used) if row.tools_used else [],
                        memory_context_used=row.memory_context_used,
                        use_tools=row.use_tools,
                        use_memory=row.use_memory,
                        error=row.error_message,
                    )
                    interactions.append(interaction)

                return interactions
        except Exception:
            logger.exception("❌ Failed to retrieve chat history")
            return []

    async def get_history_legacy(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Legacy get_history method - returns old format for backward compatibility"""
        interactions = await self.get_history(thread_id, limit)

        # Convert to old format
        legacy_history = []
        for interaction in interactions:
            legacy_history.append(
                {
                    "user_input": interaction.raw_input,
                    "agent_output": interaction.response,
                    "timestamp": interaction.timestamp.isoformat(),
                    "metadata": {
                        "timestamp": interaction.timestamp,
                        "tools_used": interaction.tools_used,
                        "use_tools": interaction.use_tools,
                        "use_memory": interaction.use_memory,
                        "had_memory_context": interaction.memory_context_used,
                        "error": interaction.error,
                    },
                }
            )

        return legacy_history

    async def close(self):
        await self.engine.dispose()
