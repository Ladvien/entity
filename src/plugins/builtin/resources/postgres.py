from __future__ import annotations

"""PostgreSQL database resource."""
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List, Optional

import asyncpg

from pipeline.observability.tracing import start_span
from pipeline.reliability import CircuitBreaker, RetryPolicy
from pipeline.stages import PipelineStage
from pipeline.state import ConversationEntry
from plugins.builtin.resources.database import DatabaseResource


class PostgresResource(DatabaseResource):
    """PostgreSQL database resource with built-in connection pooling."""

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[asyncpg.Pool] = None
        self._min_size = int(self.config.get("pool_min_size", 1))
        self._max_size = int(self.config.get("pool_max_size", 5))
        self._schema = self.config.get("db_schema")
        self._history_table = self.config.get("history_table")
        attempts = int(self.config.get("retries", 3))
        backoff = float(self.config.get("backoff", 1.0))
        self._breaker = CircuitBreaker(
            retry_policy=RetryPolicy(attempts=attempts, backoff=backoff)
        )

    async def initialize(self) -> None:
        self.logger.info("Connecting to Postgres", extra={"config": self.config})
        self._pool = await asyncpg.create_pool(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
            min_size=self._min_size,
            max_size=self._max_size,
        )
        async with self.connection() as conn:
            ext_check = await conn.fetchval(
                "SELECT COUNT(*) FROM pg_extension WHERE extname='vector'"
            )
            self.has_vector_store = bool(ext_check)
            if self._history_table:
                table = (
                    f"{asyncpg.utils._quote_ident(self._schema)}."
                    if self._schema
                    else ""
                ) + asyncpg.utils._quote_ident(self._history_table)
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

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[asyncpg.Connection]:
        """Yield a pooled database connection."""
        if self._pool is None:
            raise RuntimeError("Resource not initialized")

        async def acquire() -> asyncpg.Connection:
            return await self._pool.acquire()  # type: ignore[return-value]

        conn = await self._breaker.call(acquire)
        try:
            async with start_span("PostgresResource.connection"):
                yield conn
        finally:
            await self._pool.release(conn)

    async def health_check(self) -> bool:
        if self._pool is None:
            return False
        try:
            async with self.connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._pool is None or not self._history_table:
            return
        table = (
            f"{asyncpg.utils._quote_ident(self._schema)}." if self._schema else ""
        ) + asyncpg.utils._quote_ident(self._history_table)
        async with self.connection() as conn:
            async with start_span("PostgresResource.save_history"):
                for entry in history:
                    query = (
                        f"INSERT INTO {table} "
                        "(conversation_id, role, content, metadata, timestamp)"  # nosec B608
                        " VALUES ($1, $2, $3, $4, $5)"
                    )

                async def exec_cmd() -> str:
                    return await conn.execute(
                        query,
                        conversation_id,
                        entry.role,
                        entry.content,
                        json.dumps(entry.metadata),
                        entry.timestamp,
                    )

                await self._breaker.call(exec_cmd)

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        if self._pool is None or not self._history_table:
            return []
        table = (
            f"{asyncpg.utils._quote_ident(self._schema)}." if self._schema else ""
        ) + asyncpg.utils._quote_ident(self._history_table)
        query = (
            f"SELECT role, content, metadata, timestamp FROM {table} "  # nosec B608
            "WHERE conversation_id=$1 ORDER BY timestamp"
        )
        async with self.connection() as conn:
            async with start_span("PostgresResource.load_history"):

                async def run_fetch() -> list[asyncpg.Record]:
                    return await conn.fetch(query, conversation_id)

                rows = await self._breaker.call(run_fetch)
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

    async def _do_health_check(self, connection: asyncpg.Connection) -> None:
        await connection.fetchval("SELECT 1")
