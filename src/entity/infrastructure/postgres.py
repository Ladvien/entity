from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

import asyncpg

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool


class PostgresInfrastructure(InfrastructurePlugin):
    """Asyncpg-backed Postgres implementation."""

    name = "postgres"
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.dsn: str = self.config.get("dsn", "")
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(self._create_conn, pool_cfg, "postgres")

    async def _create_conn(self) -> asyncpg.Connection:
        return await asyncpg.connect(self.dsn)

    async def initialize(self) -> None:
        await self._pool.initialize()

    async def shutdown(self) -> None:
        while not self._pool._pool.empty():
            conn = await self._pool._pool.get()
            await conn.close()

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool as conn:
            yield conn

    def get_connection_pool(self) -> ResourcePool:
        return self._pool

    def get_pool(self) -> ResourcePool:
        return self._pool

    async def validate_runtime(self, breaker: Any | None = None) -> ValidationResult:
        """Check connectivity using a simple query."""

        if not hasattr(self._pool, "acquire"):
            return ValidationResult.error_result("connection pool unavailable")

        try:
            async with self.connection() as conn:
                await conn.execute("SELECT 1")
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
