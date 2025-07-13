from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

from entity.resources.interfaces.database import DatabaseResource
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.core.resources.container import PoolConfig, ResourcePool


class DuckDBResource(DatabaseResource):
    """Database resource backed by :class:`DuckDBInfrastructure`."""

    infrastructure_dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.database: DuckDBInfrastructure | None = None

    def get_connection_pool(self) -> ResourcePool:
        if self.database is not None:
            return self.database.get_connection_pool()
        return ResourcePool(lambda: None, PoolConfig())

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:
        if self.database is None:
            yield None
        else:
            async with self.database.connection() as conn:
                yield conn


__all__ = ["DuckDBResource"]
