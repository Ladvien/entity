from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

import duckdb

from entity.core.plugins import ResourcePlugin


class DuckDBDatabaseResource(ResourcePlugin):
    """DuckDB-backed database resource."""

    name = "duckdb_database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.path: str = self.config.get("path", ":memory:")
        self._conn: duckdb.DuckDBPyConnection | None = None

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

    async def shutdown(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
