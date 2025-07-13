from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.core.resources.container import PoolConfig, ResourcePool
from entity.core.plugins import ResourcePlugin


class DuckDBResource(ResourcePlugin):  # type: ignore[misc]
    """Lightweight database wrapper over :class:`DuckDBInfrastructure`."""

    infrastructure_dependencies = ["database_backend"]

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.database: DuckDBInfrastructure | None = None

    def get_connection_pool(self) -> ResourcePool:
        if self.database is not None:
            return self.database.get_connection_pool()
        return ResourcePool(lambda: None, PoolConfig())

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        if self.database is None:
            yield None
        else:
            async with self.database.connection() as conn:
                yield conn


__all__ = ["DuckDBResource"]
