from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from entity.infrastructure.postgres import PostgresInfrastructure
from entity.core.resources.container import PoolConfig, ResourcePool
from entity.core.plugins import ResourcePlugin


class PostgresResource(ResourcePlugin):  # type: ignore[misc]
    """Database interface over :class:`PostgresInfrastructure`."""

    infrastructure_dependencies = ["database_backend"]

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.database_backend: PostgresInfrastructure | None = None

    def get_connection_pool(self) -> ResourcePool:
        if self.database_backend is not None:
            return self.database_backend.get_connection_pool()
        return ResourcePool(lambda: None, PoolConfig())

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        if self.database_backend is None:
            yield None
        else:
            async with self.database_backend.connection() as conn:
                yield conn

    @property
    def database(self) -> PostgresInfrastructure | None:
        return self.database_backend

    @database.setter
    def database(self, value: PostgresInfrastructure | None) -> None:
        self.database_backend = value


__all__ = ["PostgresResource"]
