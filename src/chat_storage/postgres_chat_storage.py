# src/storage/postgres.py - FIXED VERSION

import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from sqlalchemy import text

from src.service.config import StorageConfig
from src.chat_storage.base_chat_storage import BaseChatStorage
from src.shared.models import ChatInteraction
from src.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PostgresChatStorage(BaseChatStorage):
    """PostgreSQL storage using centralized DatabaseConnection"""

    def __init__(
        self, db_connection: DatabaseConnection, storage_config: StorageConfig
    ):
        self.db_connection = db_connection
        self.storage_config = storage_config
        logger.info(f"🔧 PostgresChatStorage initialized with centralized connection")

    async def initialize(self):
        """Initialize the storage tables"""
        if not self.storage_config.init_on_startup:
            logger.info("⏭️ Skipping storage initialization (init_on_startup=False)")
            return

        try:
            # Use the centralized connection's schema management
            await self.db_connection.ensure_schema()

            # Create the table using the centralized connection
            create_table_sql = f"""
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

            # Create indexes
            index_commands = [
                f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_interaction_id ON {self.storage_config.history_table}(interaction_id)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_thread_id ON {self.storage_config.history_table}(thread_id)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_timestamp ON {self.storage_config.history_table}(timestamp DESC)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_thread_timestamp ON {self.storage_config.history_table}(thread_id, timestamp DESC)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.storage_config.history_table}_user_id ON {self.storage_config.history_table}(user_id) WHERE user_id IS NOT NULL",
            ]

            # Execute all commands using centralized connection
            all_commands = [create_table_sql] + index_commands
            await self.db_connection.execute_schema_commands(all_commands)

            logger.info(
                f"✅ Table '{self.db_connection.schema}.{self.storage_config.history_table}' ready with ChatInteraction support"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    async def save_interaction(self, interaction: ChatInteraction):
        """Save a ChatInteraction to the database using centralized connection"""
        try:
            session = await self.db_connection.get_session()
            async with session:
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
        """Get chat history as list of ChatInteraction objects using centralized connection"""
        try:
            session = await self.db_connection.get_session()
            async with session:
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
        """Get a specific interaction by its ID using centralized connection"""
        try:
            session = await self.db_connection.get_session()
            async with session:
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
        """Close the database connection"""
        await self.db_connection.close()
        logger.info("✅ PostgresChatStorage closed")
