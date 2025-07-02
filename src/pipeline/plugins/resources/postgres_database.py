from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

import asyncpg

from pipeline.base_plugins import ResourcePlugin
from pipeline.context import ConversationEntry
<<<<<<< HEAD:src/pipeline/plugins/resources/postgres.py
from pipeline.stages import PipelineStage


class ConnectionPoolResource(ResourcePlugin):
    """Generic async connection pool resource."""

    stages = [PipelineStage.PARSE]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[Any] = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    async def acquire(self) -> Any:
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        return await self._pool.acquire()

    async def release(self, connection: Any) -> None:
        if self._pool is not None:
            await self._pool.release(connection)

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    async def health_check(self) -> bool:
        if self._pool is None:
            return False
        async with self.connection() as conn:
            try:
                await self._do_health_check(conn)
                return True
            except Exception:
                return False

    async def _do_health_check(self, connection: Any) -> None:
        raise NotImplementedError


class PostgresPoolResource(ConnectionPoolResource):
    """Asynchronous PostgreSQL connection pool.
=======
from pipeline.resources.database import DatabaseResource
from pipeline.stages import PipelineStage


class PostgresDatabaseResource(DatabaseResource):
    """Asynchronous PostgreSQL connection resource.
>>>>>>> 66045f0cc3ea9a831e3ec579ceb40548cd673716:src/pipeline/plugins/resources/postgres_database.py

    Highlights **Configuration Over Code (9)** by defining all connection
    details in YAML rather than hardcoding them in the class.
    """

    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
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
        ext_check = await self._connection.fetchval(
            "SELECT COUNT(*) FROM pg_extension WHERE extname='vector'"
        )
        self.has_vector_store = bool(ext_check)
        if self._history_table:
            table = f"{self._schema + '.' if self._schema else ''}{self._history_table}"
            async with self.connection() as conn:
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

    async def _do_health_check(self, connection: asyncpg.Connection) -> None:
        await connection.fetchval("SELECT 1")

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
PostgresResource = PostgresPoolResource
