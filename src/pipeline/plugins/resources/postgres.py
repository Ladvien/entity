from __future__ import annotations

from typing import Any, Dict, List

import asyncpg
from asyncpg.utils import _quote_ident

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage

from .postgres_pool import PostgresConnectionPool


class PostgresResource(ResourcePlugin):
    """Asynchronous PostgreSQL connection pool resource.

    Configuration keys mirror standard connection parameters. Optional
    ``db_schema`` and ``history_table`` enable conversation persistence.
    """

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        """Initialize the connection pool wrapper."""
        super().__init__(config)
        self._pool = PostgresConnectionPool(self.config)
        self._schema = self.config.get("db_schema")
        self._history_table = self.config.get("history_table")

    def _qualified_history_table(self) -> str:
        """Return ``history_table`` with schema prefix if provided."""
        table = _quote_ident(self._history_table)
        if self._schema:
            schema = _quote_ident(self._schema)
            return f"{schema}.{table}"
        return table

    async def initialize(self) -> None:
        """Create the pool and optional history table."""
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

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        """No-op; this resource does not execute in the pipeline."""
        return None

    async def health_check(self) -> bool:
        """Return ``True`` if the database connection is healthy."""
        return await self._pool.health_check()

    async def execute(self, query: str, *args: Any) -> None:  # type: ignore[override]
        """Execute a statement within the pool."""
        async with self._pool.connection() as conn:
            await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        """Return a list of ``asyncpg.Record`` from ``query``."""
        async with self._pool.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        """Return a single row for ``query`` or ``None``."""
        async with self._pool.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Return a single value for ``query``."""
        async with self._pool.connection() as conn:
            return await conn.fetchval(query, *args)
