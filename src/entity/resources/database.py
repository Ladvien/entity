from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from entity.core.resources.container import PoolConfig, ResourcePool
from entity.plugins.base import ResourcePlugin
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.infrastructure.postgres import PostgresInfrastructure


class DatabaseResource(ResourcePlugin):
    """Abstract database interface over a concrete backend."""

    infrastructure_dependencies = ["database_backend"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    def get_connection_pool(self) -> ResourcePool:
        infrastructure = getattr(self, "database", None)
        if infrastructure:
            return infrastructure.get_connection_pool()
        return ResourcePool(lambda: None, PoolConfig())

    def get_pool(self) -> ResourcePool:
        return self.get_connection_pool()

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:  # pragma: no cover - stub
        yield None


class DuckDBResource(DatabaseResource):  # type: ignore[misc]
    """Lightweight database wrapper over :class:`DuckDBInfrastructure`."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._database: DuckDBInfrastructure | None = None
        self._database_backend: DuckDBInfrastructure | None = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        if self.database is None:
            yield None
        else:
            async with self.database.connection() as conn:
                yield conn

    @property
    def database(self) -> DuckDBInfrastructure | None:
        return self._database

    @database.setter
    def database(self, value: DuckDBInfrastructure | None) -> None:
        self._database = value

    @property
    def database_backend(self) -> DuckDBInfrastructure | None:
        return self._database_backend

    @database_backend.setter
    def database_backend(self, value: DuckDBInfrastructure | None) -> None:
        self._database_backend = value
        self._database = value


class PostgresResource(DatabaseResource):  # type: ignore[misc]
    """Database interface over :class:`PostgresInfrastructure`."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._database: PostgresInfrastructure | None = None
        self._database_backend: PostgresInfrastructure | None = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        if self.database is None:
            yield None
        else:
            async with self.database.connection() as conn:
                yield conn

    @property
    def database(self) -> PostgresInfrastructure | None:
        return self._database

    @database.setter
    def database(self, value: PostgresInfrastructure | None) -> None:
        self._database = value

    @property
    def database_backend(self) -> PostgresInfrastructure | None:
        return self._database_backend

    @database_backend.setter
    def database_backend(self, value: PostgresInfrastructure | None) -> None:
        self._database_backend = value
        self._database = value


__all__ = ["DatabaseResource", "DuckDBResource", "PostgresResource"]
