# entity_service/storage/postgres.py

import json
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any
import logging
from datetime import datetime

from src.service.config import DatabaseConfig, StorageConfig
from src.storage.base import ChatStorage


logger = logging.getLogger(__name__)


class PostgresChatStorage(ChatStorage):
    def __init__(self, db_config: DatabaseConfig, storage_config: StorageConfig):
        self.db_config = db_config
        self.storage_config = storage_config

        self.conn_url = (
            f"postgresql+asyncpg://{db_config.username}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.name}"
        )
        self.engine = create_async_engine(self.conn_url, echo=False)
        self.session_factory = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def initialize(self):
        if not self.storage_config.init_on_startup:
            return

        async with self.engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.storage_config.history_table} (
                        id SERIAL PRIMARY KEY,
                        thread_id TEXT NOT NULL,
                        user_input TEXT NOT NULL,
                        agent_output TEXT NOT NULL,
                        metadata JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
        logger.info("✅ Postgres chat history table ready")

    async def save_interaction(
        self,
        thread_id: str,
        user_input: str,
        agent_output: str,
        metadata: Dict[str, Any],
    ):
        try:
            async with self.session_factory() as session:
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.storage_config.history_table}
                        (thread_id, user_input, agent_output, metadata)
                        VALUES (:thread_id, :user_input, :agent_output, :metadata)
                        """
                    ),
                    {
                        "thread_id": thread_id,
                        "user_input": user_input,
                        "agent_output": agent_output,
                        "metadata": json.dumps(metadata, default=str),
                    },
                )
                await session.commit()
            logger.debug("💾 Chat interaction saved")
        except Exception:
            logger.exception("❌ Failed to store chat interaction")

    async def get_history(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        f"""
                        SELECT user_input, agent_output, metadata, timestamp
                        FROM {self.storage_config.history_table}
                        WHERE thread_id = :thread_id
                        ORDER BY timestamp DESC
                        LIMIT :limit
                        """
                    ),
                    {"thread_id": thread_id, "limit": limit},
                )
                rows = result.fetchall()
                return [
                    {
                        "user_input": row.user_input,
                        "agent_output": row.agent_output,
                        "metadata": row.metadata,
                        "timestamp": row.timestamp.isoformat(),
                    }
                    for row in rows
                ]
        except Exception:
            logger.exception("❌ Failed to retrieve chat history")
            return []

    async def close(self):
        await self.engine.dispose()
