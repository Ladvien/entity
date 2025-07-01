from __future__ import annotations

from typing import Any, Dict, List

import asyncpg

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

    async def initialize(self) -> None:
        await self._pool.initialize()

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
