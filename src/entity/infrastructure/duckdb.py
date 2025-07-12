from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

from pipeline.exceptions import CircuitBreakerTripped
from pipeline.reliability import CircuitBreaker

import duckdb

from entity.core.plugins import InfrastructurePlugin, ValidationResult


class DuckDBInfrastructure(InfrastructurePlugin):
    """DuckDB-backed database implementation."""

    name = "duckdb_database"
    infrastructure_type = "database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.path: str = self.config.get("path", ":memory:")
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60.0),
        )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        """Open the database connection."""
        self._conn = duckdb.connect(self.path)

    @asynccontextmanager
    async def connection(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Yield a connection to execute queries."""
        if self._conn is None:
            self._conn = duckdb.connect(self.path)
        try:
            yield self._conn
        finally:
            pass

    def get_connection_pool(self) -> duckdb.DuckDBPyConnection:
        """Return the shared DuckDB connection."""
        if self._conn is None:
            self._conn = duckdb.connect(self.path)
        return self._conn

    async def shutdown(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    async def validate_runtime(self) -> ValidationResult:
        """Check connectivity using a simple query."""

        async def _query() -> None:
            async with self.connection() as conn:
                conn.execute("SELECT 1")

        try:
            await self._breaker.call(_query)
        except CircuitBreakerTripped:
            return ValidationResult.error_result("circuit breaker open")
        except Exception as exc:  # noqa: BLE001 - return as validation error
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
