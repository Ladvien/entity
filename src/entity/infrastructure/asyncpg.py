from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, AsyncIterator

import asyncpg

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool
from entity.config.models import AsyncPGConfig


class AsyncPGInfrastructure(InfrastructurePlugin):
    """PostgreSQL infrastructure using asyncpg."""

    name = "asyncpg"
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.dsn: str = self.config.get("dsn", "")
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(self._create_conn, pool_cfg, "asyncpg")

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            AsyncPGConfig(**config)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        metrics = getattr(self, "metrics_collector", None)
        if metrics is not None:
            self._pool.set_metrics_collector(metrics)
        await self._pool.initialize()

    async def _create_conn(self) -> asyncpg.Connection:
        return await asyncpg.connect(self.dsn)

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool as conn:
            yield conn

    def get_connection_pool(self) -> ResourcePool:
        return self._pool

    def get_pool(self) -> ResourcePool:
        return self._pool

    async def shutdown(self) -> None:
        while not self._pool._pool.empty():
            conn = await self._pool._pool.get()
            await conn.close()

    async def validate_runtime(self, breaker: Any | None = None) -> ValidationResult:
        try:
            async with self.connection() as conn:
                await conn.execute("SELECT 1")
            return ValidationResult.success_result()
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))


__all__ = ["AsyncPGInfrastructure"]
