from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict

from pipeline.exceptions import CircuitBreakerTripped
from pipeline.reliability import CircuitBreaker

from entity.core.plugins import InfrastructurePlugin, ValidationResult


class _DummyConn:
    async def execute(self, *args: Any, **kwargs: Any) -> None:
        return None


class _DummyPool:
    async def acquire(self) -> _DummyConn:
        return _DummyConn()

    async def release(self, _conn: _DummyConn) -> None:
        return None

    async def close(self) -> None:  # pragma: no cover - placeholder
        return None


class PostgresInfrastructure(InfrastructurePlugin):
    """Minimal Postgres infrastructure stub used in tests."""

    name = "postgres"
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._pool = _DummyPool()
        self._breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60.0),
        )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        return None

    @asynccontextmanager
    async def connection(self) -> Any:
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

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
