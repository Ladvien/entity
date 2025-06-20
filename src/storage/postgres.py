# Quick fix for your existing src/storage/postgres.py

import json
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any, Optional
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

        schema = getattr(db_config, "db_schema", None) or "public"

        logger.info(f"🔧 Database schema: {schema}")

        # Basic connection URL without options
        self.conn_url = (
            f"postgresql+asyncpg://{db_config.username}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.name}"
        )

        # Create engine with schema in connect_args ONLY if not public
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

        # Fix: Use db_schema field from config
        schema = getattr(self.db_config, "db_schema", None) or "public"

        try:
            async with self.engine.begin() as conn:
                # Create schema if it doesn't exist (skip for public schema)
                if schema != "public":
                    await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                    logger.info(f"✅ Schema '{schema}' ready")

                # Set search path for this session
                if schema != "public":
                    await conn.execute(text(f"SET search_path TO {schema}"))

                # Create the table first
                await conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self.storage_config.history_table} (
                            id SERIAL PRIMARY KEY,
                            
                            -- Core interaction fields
                            interaction_id TEXT UNIQUE NOT NULL,
                            thread_id TEXT NOT NULL,
                            timestamp TIMESTAMP NOT NULL,
                            
                            -- Content fields
                            response TEXT NOT NULL,
                            raw_input TEXT NOT NULL,
                            raw_output TEXT NOT NULL,
                            
                            -- Tool and memory usage
                            tools_used JSONB DEFAULT '[]'::jsonb,
                            memory_context_used BOOLEAN DEFAULT FALSE,
                            memory_context TEXT DEFAULT '',
                            
                            -- Configuration
                            use_tools BOOLEAN DEFAULT TRUE,
                            use_memory BOOLEAN DEFAULT TRUE,
                            
                            -- Error handling
                            error_message TEXT,
                            
                            -- Performance metrics
                            response_time_ms FLOAT,
                            token_count INTEGER,
                            
                            -- Conversation metadata
                            conversation_turn INTEGER,
                            user_id TEXT,
                            
                            -- Agent personality tracking
                            agent_personality_applied BOOLEAN DEFAULT FALSE,
                            personality_adjustments JSONB DEFAULT '[]'::jsonb,
                            
                            -- Extended metadata
                            metadata JSONB DEFAULT '{{}}'::jsonb,
                            
                            -- Constraints
                            CONSTRAINT valid_thread_id CHECK (length(thread_id) > 0),
                            CONSTRAINT valid_interaction_id CHECK (length(interaction_id) > 0)
                        )
                        """
                    )
                )

                # Create indexes separately
                index_commands = [
                    f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_interaction_id ON {self.storage_config.history_table}(interaction_id)",
                    f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_thread_id ON {self.storage_config.history_table}(thread_id)",
                    f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_timestamp ON {self.storage_config.history_table}(timestamp DESC)",
                    f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_thread_timestamp ON {self.storage_config.history_table}(thread_id, timestamp DESC)",
                    f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_user_id ON {self.storage_config.history_table}(user_id) WHERE user_id IS NOT NULL",
                ]

                for index_cmd in index_commands:
                    await conn.execute(text(index_cmd))

                logger.info(
                    f"✅ Table '{schema}.{self.storage_config.history_table}' ready with ChatInteraction support"
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
                        (interaction_id, thread_id, timestamp, response, raw_input, raw_output, 
                         tools_used, memory_context_used, memory_context, use_tools, use_memory, 
                         error_message, response_time_ms, token_count, conversation_turn, user_id,
                         agent_personality_applied, personality_adjustments, metadata)
                        VALUES (:interaction_id, :thread_id, :timestamp, :response, :raw_input, :raw_output,
                               :tools_used, :memory_context_used, :memory_context, :use_tools, :use_memory,
                               :error_message, :response_time_ms, :token_count, :conversation_turn, :user_id,
                               :agent_personality_applied, :personality_adjustments, :metadata)
                        ON CONFLICT (interaction_id) DO UPDATE SET
                            response = EXCLUDED.response,
                            raw_output = EXCLUDED.raw_output,
                            tools_used = EXCLUDED.tools_used,
                            memory_context_used = EXCLUDED.memory_context_used,
                            memory_context = EXCLUDED.memory_context,
                            error_message = EXCLUDED.error_message,
                            response_time_ms = EXCLUDED.response_time_ms,
                            token_count = EXCLUDED.token_count,
                            agent_personality_applied = EXCLUDED.agent_personality_applied,
                            personality_adjustments = EXCLUDED.personality_adjustments,
                            metadata = EXCLUDED.metadata
                        """
                    ),
                    {
                        "interaction_id": interaction.interaction_id,
                        "thread_id": interaction.thread_id,
                        "timestamp": interaction.timestamp,
                        "response": interaction.response,
                        "raw_input": interaction.raw_input,
                        "raw_output": interaction.raw_output,
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
                await session.commit()
            logger.debug(
                f"💾 ChatInteraction saved: {interaction.interaction_id[:8]}..."
            )
        except Exception as e:
            logger.exception(f"❌ Failed to store chat interaction: {e}")
            raise

    async def get_history(
        self, thread_id: str, limit: int = 100
    ) -> List[ChatInteraction]:
        """Get chat history as list of ChatInteraction objects"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        f"""
                        SELECT interaction_id, thread_id, timestamp, response, raw_input, raw_output,
                               tools_used, memory_context_used, memory_context, use_tools, use_memory, 
                               error_message, response_time_ms, token_count, conversation_turn, user_id,
                               agent_personality_applied, personality_adjustments, metadata
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
                    # Parse JSON fields safely
                    tools_used = []
                    if row.tools_used:
                        try:
                            tools_used = json.loads(row.tools_used)
                        except (json.JSONDecodeError, TypeError):
                            tools_used = []

                    personality_adjustments = []
                    if row.personality_adjustments:
                        try:
                            personality_adjustments = json.loads(
                                row.personality_adjustments
                            )
                        except (json.JSONDecodeError, TypeError):
                            personality_adjustments = []

                    metadata = {}
                    if row.metadata:
                        try:
                            metadata = json.loads(row.metadata)
                        except (json.JSONDecodeError, TypeError):
                            metadata = {}

                    interaction = ChatInteraction(
                        response=row.response,
                        thread_id=row.thread_id,
                        raw_input=row.raw_input,
                        timestamp=row.timestamp,
                        raw_output=row.raw_output or row.response,
                        tools_used=tools_used,
                        memory_context_used=row.memory_context_used or False,
                        memory_context=row.memory_context or "",
                        use_tools=row.use_tools if row.use_tools is not None else True,
                        use_memory=(
                            row.use_memory if row.use_memory is not None else True
                        ),
                        error=row.error_message,
                        response_time_ms=row.response_time_ms,
                        token_count=row.token_count,
                        conversation_turn=row.conversation_turn,
                        user_id=row.user_id,
                        agent_personality_applied=row.agent_personality_applied
                        or False,
                        personality_adjustments=personality_adjustments,
                        metadata=metadata,
                        interaction_id=row.interaction_id,
                    )
                    interactions.append(interaction)

                return interactions
        except Exception as e:
            logger.exception(f"❌ Failed to retrieve chat history: {e}")
            return []

    async def get_interaction_by_id(
        self, interaction_id: str
    ) -> Optional[ChatInteraction]:
        """Get a specific interaction by its ID"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        f"""
                        SELECT interaction_id, thread_id, timestamp, response, raw_input, raw_output,
                               tools_used, memory_context_used, memory_context, use_tools, use_memory, 
                               error_message, response_time_ms, token_count, conversation_turn, user_id,
                               agent_personality_applied, personality_adjustments, metadata
                        FROM {self.storage_config.history_table}
                        WHERE interaction_id = :interaction_id
                        """
                    ),
                    {"interaction_id": interaction_id},
                )
                row = result.fetchone()

                if not row:
                    return None

                # Parse JSON fields safely (same as in get_history)
                tools_used = json.loads(row.tools_used) if row.tools_used else []
                personality_adjustments = (
                    json.loads(row.personality_adjustments)
                    if row.personality_adjustments
                    else []
                )
                metadata = json.loads(row.metadata) if row.metadata else {}

                return ChatInteraction(
                    response=row.response,
                    thread_id=row.thread_id,
                    raw_input=row.raw_input,
                    timestamp=row.timestamp,
                    raw_output=row.raw_output or row.response,
                    tools_used=tools_used,
                    memory_context_used=row.memory_context_used or False,
                    memory_context=row.memory_context or "",
                    use_tools=row.use_tools if row.use_tools is not None else True,
                    use_memory=row.use_memory if row.use_memory is not None else True,
                    error=row.error_message,
                    response_time_ms=row.response_time_ms,
                    token_count=row.token_count,
                    conversation_turn=row.conversation_turn,
                    user_id=row.user_id,
                    agent_personality_applied=row.agent_personality_applied or False,
                    personality_adjustments=personality_adjustments,
                    metadata=metadata,
                    interaction_id=row.interaction_id,
                )
        except Exception as e:
            logger.exception(f"❌ Failed to retrieve interaction {interaction_id}: {e}")
            return None

    async def close(self):
        await self.engine.dispose()
