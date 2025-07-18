from __future__ import annotations

from contextlib import asynccontextmanager

from entity.infrastructure import DuckDBInfrastructure, PostgresInfrastructure


class FailingDuckDBInfrastructure(DuckDBInfrastructure):
    """DuckDB plugin that always fails during runtime validation."""

    name = "failing_duckdb"

    @asynccontextmanager
    async def connection(self):  # type: ignore[override]
        class BadConn:
            def execute(self, _q):
                raise RuntimeError("boom")

            def close(self):
                pass

        yield BadConn()


class FailingPostgresInfrastructure(PostgresInfrastructure):
    """Postgres plugin that always fails during runtime validation."""

    name = "failing_postgres"

    async def initialize(self) -> None:  # type: ignore[override]
        """Skip real connection setup."""
        return None

    @asynccontextmanager
    async def connection(self):  # type: ignore[override]
        class BadConn:
            async def execute(self, *args, **kwargs):
                raise RuntimeError("bad")

        yield BadConn()
