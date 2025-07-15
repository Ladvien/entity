from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

from entity.core.resources.container import PoolConfig, ResourcePool

from entity.core.plugins import ResourcePlugin


class DatabaseResource(ResourcePlugin):
    """Abstract database interface over a concrete backend."""

    infrastructure_dependencies = ["database_backend"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    def get_connection_pool(self) -> ResourcePool:  # pragma: no cover - stub
        """Return the connection pool from the injected infrastructure."""
        infrastructure = getattr(self, "database", None)
        if infrastructure:
            return infrastructure.get_connection_pool()
        return ResourcePool(lambda: None, PoolConfig())

    def get_pool(self) -> ResourcePool:
        """Return a connection pool for one-time use."""
        return self.get_connection_pool()

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:  # pragma: no cover - stub
        yield None
