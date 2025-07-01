from __future__ import annotations

from typing import Any, Dict, List

import asyncpg
from asyncpg.utils import _quote_ident

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage

from .postgres_pool import PostgresConnectionPool


class PostgresResource(ResourcePlugin):
    """Thin wrapper around an asyncpg connection pool."""

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool = PostgresConnectionPool(self.config)
        self._schema = self.config.get("db_schema")
        self._history_table = self.config.get("history_table")

    def _qualified_history_table(self) -> str:
        table = _quote_ident(self._history_table)
        if self._schema:
            schema = _quote_ident(self._schema)
            return f"{schema}.{table}"
        return table

    async def initialize(self) -> None:
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
        return None

    async def health_check(self) -> bool:
        return await self._pool.health_check()

    async def execute(self, query: str, *args: Any) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        async with self._pool.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        async with self._pool.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        async with self._pool.connection() as conn:
            return await conn.fetchval(query, *args)
