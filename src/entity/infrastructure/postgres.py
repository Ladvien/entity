from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict

from entity.pipeline.exceptions import CircuitBreakerTripped
from entity.core.circuit_breaker import CircuitBreaker

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool


class _DummyConn:
    async def execute(
        self, *args: Any, **kwargs: Any
    ) -> None:  # pragma: no cover - stub
        return None


async def _create_conn() -> _DummyConn:
    return _DummyConn()


class PostgresInfrastructure(InfrastructurePlugin):
    """Minimal Postgres infrastructure stub used in tests."""

    name = "postgres"
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(_create_conn, pool_cfg)
        self._breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60.0),
        )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        await self._pool.initialize()

    @asynccontextmanager
    async def connection(self) -> Any:
        async with self._pool as conn:
            yield conn

    def get_connection_pool(self) -> Any:
        """Return the underlying connection pool."""
        return self._pool

    async def validate_runtime(
        self, breaker: CircuitBreaker | None = None
    ) -> ValidationResult:
        """Check connectivity using a simple query."""

        if not hasattr(self._pool, "acquire"):
            return ValidationResult.error_result("connection pool unavailable")

        async def _query() -> None:
            async with self.connection() as conn:
                await conn.execute("SELECT 1")

        breaker = breaker or self._breaker
        try:
            await breaker.call(_query)
        except CircuitBreakerTripped:
            return ValidationResult.error_result("circuit breaker open")
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
