from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import asyncpg

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class PostgresConnectionPool(ResourcePlugin):
    """Asynchronous PostgreSQL connection pool.

    Highlights **Configuration Over Code (9)** by defining all connection
    details in YAML rather than hardcoding them in the class.
    """

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[asyncpg.Pool] = None
        self._schema = self.config.get("db_schema")
        self._history_table = self.config.get("history_table")

    async def initialize(self) -> None:
        self.logger.info(
            "Creating Postgres connection pool", extra={"config": self.config}
        )
        self._pool = await asyncpg.create_pool(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
        )
        if self._history_table:
            table = f"{self._schema + '.' if self._schema else ''}{self._history_table}"
            async with self.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        conversation_id TEXT,
                        role TEXT,
                        content TEXT,
                        metadata JSONB,
                        timestamp TIMESTAMPTZ
                    )
                    """
                )

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        return None

    async def acquire(self) -> asyncpg.Connection:
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        return await self._pool.acquire()

    async def release(self, connection: asyncpg.Connection) -> None:
        if self._pool is not None:
            await self._pool.release(connection)

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    async def health_check(self) -> bool:
        if self._pool is None:
            return False
        conn = await self.acquire()
        try:
            await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
        finally:
            await self.release(conn)

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        """Persist conversation ``history`` for ``conversation_id``."""

        if self._pool is None or not self._history_table:
            return

        table = f"{self._schema + '.' if self._schema else ''}{self._history_table}"
        for entry in history:
            query = (
                f"INSERT INTO {table} "
                "(conversation_id, role, content, metadata, timestamp)"  # nosec B608
                " VALUES ($1, $2, $3, $4, $5)"
            )
            await self._pool.execute(
                query,
                conversation_id,
                entry.role,
                entry.content,
                json.dumps(entry.metadata),
                entry.timestamp,
            )

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        """Retrieve stored history for ``conversation_id``."""

        if self._pool is None or not self._history_table:
            return []

        table = f"{self._schema + '.' if self._schema else ''}{self._history_table}"
        query = (
            f"SELECT role, content, metadata, timestamp FROM {table} "  # nosec B608
            "WHERE conversation_id=$1 ORDER BY timestamp"
        )
        rows = await self._pool.fetch(query, conversation_id)
        history: List[ConversationEntry] = []
        for row in rows:
            metadata = row["metadata"]
            if not isinstance(metadata, dict):
                metadata = json.loads(metadata) if metadata else {}
            history.append(
                ConversationEntry(
                    content=row["content"],
                    role=row["role"],
                    timestamp=row["timestamp"],
                    metadata=metadata,
                )
            )
        return history


# Backwards compatibility alias
PostgresResource = PostgresConnectionPool
