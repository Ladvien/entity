from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

from entity.core.resources.container import PoolConfig, ResourcePool

from entity.core.plugins import ResourcePlugin


class DatabaseResource(ResourcePlugin):
    """Abstract database interface over a concrete backend."""

    infrastructure_dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    def get_connection_pool(self) -> ResourcePool:  # pragma: no cover - stub
        """Return the shared connection pool from the infrastructure."""
        infra = getattr(self, "database", None)
        if infra is not None:
            return infra.get_connection_pool()
        return ResourcePool(lambda: None, PoolConfig())

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:  # pragma: no cover - stub
        pool = self.get_connection_pool()
        async with pool as conn:
            yield conn
