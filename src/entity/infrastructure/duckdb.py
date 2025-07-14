from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator
import os

from entity.pipeline.exceptions import CircuitBreakerTripped
from entity.core.circuit_breaker import CircuitBreaker

import importlib

try:
    duckdb = importlib.import_module("duckdb")
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    duckdb = None

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool


class DuckDBInfrastructure(InfrastructurePlugin):
    """DuckDB-backed database implementation."""

    name = "duckdb_database"
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.path: str = self.config.get("path", ":memory:")
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(self._create_conn, pool_cfg, "duckdb")
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60.0),
        )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if duckdb is None:
            print(
                "DuckDB not installed. Run 'poetry install --with dev' to enable local storage."
            )
            return
        metrics = getattr(self, "metrics_collector", None)
        if metrics is not None:
            self._pool.set_metrics_collector(metrics)
        await self._pool.initialize()

    async def _create_conn(self) -> duckdb.DuckDBPyConnection:
        if duckdb is None:
            raise RuntimeError(
                "DuckDB missing. Install with 'poetry install --with dev'."
            )
        return duckdb.connect(self.path)

    @asynccontextmanager
    async def connection(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Yield an existing connection or acquire one from the pool."""
        if duckdb is None:
            raise RuntimeError(
                "DuckDB missing. Install with 'poetry install --with dev'."
            )
        if self._conn is not None:
            yield self._conn
        else:
            async with self._pool as conn:
                yield conn

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

        if duckdb is None:
            return ValidationResult.error_result(
                "duckdb package missing. Run 'poetry install --with dev'."
            )

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
