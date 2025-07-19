from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator
import os

import importlib

try:
    duckdb = importlib.import_module("duckdb")
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    duckdb = None

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool
from entity.config.models import DuckDBConfig


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

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            DuckDBConfig(**config)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        """Prepare the database for use."""
        if duckdb is None:
            print(
                "DuckDB not installed. Run 'poetry install --with dev' to enable local storage."
            )
            return

    async def _create_conn(self) -> duckdb.DuckDBPyConnection:
        if duckdb is None:
            raise RuntimeError(
                "DuckDB missing. Install with 'poetry install --with dev'."
            )
        return duckdb.connect(self.path)

    @asynccontextmanager
    async def connection(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Yield a new DuckDB connection."""
        if duckdb is None:
            raise RuntimeError(
                "DuckDB missing. Install with 'poetry install --with dev'."
            )
        conn = duckdb.connect(self.path)
        try:
            yield conn
        finally:
            conn.close()

    async def shutdown(self) -> None:
        pass

    def get_connection_pool(self) -> ResourcePool:
        return ResourcePool(self._create_conn, PoolConfig(), "duckdb")

    def get_pool(self) -> ResourcePool:
        """Return a connection pool for one-time use."""
        return self.get_connection_pool()

    async def validate_runtime(self, breaker: Any | None = None) -> ValidationResult:
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

        try:
            async with self.connection() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:  # noqa: BLE001 - return as validation error
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
