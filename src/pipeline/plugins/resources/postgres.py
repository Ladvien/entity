from __future__ import annotations

<<<<<<< HEAD
from typing import Any, Dict, List
=======
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc

import asyncpg
from asyncpg.utils import _quote_ident

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage

from .postgres_pool import PostgresConnectionPool


<<<<<<< HEAD
class PostgresResource(ResourcePlugin):
    """Thin wrapper around an asyncpg connection pool."""
=======
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

    Highlights **Configuration Over Code (9)** by defining all connection
    details in YAML rather than hardcoding them in the class.
    """
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc

    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
<<<<<<< HEAD
        self._pool = PostgresConnectionPool(self.config)
=======
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc
        self._schema = self.config.get("db_schema")
        self._history_table = self.config.get("history_table")

    def _qualified_history_table(self) -> str:
        table = _quote_ident(self._history_table)
        if self._schema:
            schema = _quote_ident(self._schema)
            return f"{schema}.{table}"
        return table

    async def initialize(self) -> None:
<<<<<<< HEAD
        await self._pool.initialize()
        if self._history_table:
            table = self._qualified_history_table()
            query = f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata JSONB,
                    timestamp TIMESTAMPTZ
                )
            """
            await self.execute(query)
=======
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
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        return None

<<<<<<< HEAD
    async def health_check(self) -> bool:
        return await self._pool.health_check()
=======
    async def _do_health_check(self, connection: asyncpg.Connection) -> None:
        await connection.fetchval("SELECT 1")
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc

    async def execute(self, query: str, *args: Any) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(query, *args)

<<<<<<< HEAD
    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        async with self._pool.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        async with self._pool.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        async with self._pool.connection() as conn:
            return await conn.fetchval(query, *args)
=======
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
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc
