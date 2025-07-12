from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator
import os

from pipeline.exceptions import CircuitBreakerTripped
from pipeline.reliability import CircuitBreaker

import duckdb

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool


class DuckDBInfrastructure(InfrastructurePlugin):
    """DuckDB-backed database implementation."""

    name = "duckdb_database"
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.path: str = self.config.get("path", ":memory:")
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(self._create_conn, pool_cfg)
        self._breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60.0),
        )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        await self._pool.initialize()

    async def _create_conn(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.path)

    @asynccontextmanager
    async def connection(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Yield a connection from the pool."""
        async with self._pool as conn:
            yield conn

    def get_connection_pool(self) -> duckdb.DuckDBPyConnection:
        """Return the shared DuckDB connection."""
        if self._conn is None:
            self._conn = duckdb.connect(self.path)
        return self._conn

    async def shutdown(self) -> None:
        while not self._pool._pool.empty():
            conn = await self._pool._pool.get()
            conn.close()

    def get_connection_pool(self) -> ResourcePool:
        return self._pool

    async def validate_runtime(
        self, breaker: CircuitBreaker | None = None
    ) -> ValidationResult:
        """Check connectivity using a simple query."""

        if self.path != ":memory:":
            directory = os.path.dirname(self.path) or "."
            if not os.path.exists(directory):
                return ValidationResult.error_result(
                    f"database directory missing: {directory}"
                )
            if not os.access(directory, os.W_OK):
                return ValidationResult.error_result(
                    f"database directory not writable: {directory}"
                )

        async def _query() -> None:
            async with self.connection() as conn:
                conn.execute("SELECT 1")

        breaker = breaker or self._breaker
        try:
            await breaker.call(_query)
        except CircuitBreakerTripped:
            return ValidationResult.error_result("circuit breaker open")
        except Exception as exc:  # noqa: BLE001 - return as validation error
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
