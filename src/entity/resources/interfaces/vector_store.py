from __future__ import annotations

from typing import Dict, List

from entity.core.plugins import ResourcePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool
from contextlib import asynccontextmanager


class VectorStoreResource(ResourcePlugin):
    """Abstract vector store interface."""

    infrastructure_dependencies = ["vector_store"]
    resource_category = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._pool: ResourcePool | None = None

    async def initialize(self) -> None:
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(self._create_client, pool_cfg, "vector_store")
        metrics = getattr(self, "metrics_collector", None)
        if metrics is None:
            container = getattr(self, "resource_container", None)
            if container is not None:
                metrics = container.get("metrics_collector")
        if metrics is not None:
            self._pool.set_metrics_collector(metrics)
        await self._pool.initialize()

    async def _create_client(self) -> "VectorStoreResource":
        return self

    def get_connection_pool(self) -> ResourcePool:
        return self._pool or ResourcePool(lambda: self, PoolConfig())

    def get_pool_metrics(self) -> Dict[str, int]:
        if self._pool is None:
            return {"total_size": 0, "in_use": 0, "available": 0}
        return self._pool.metrics()

    @asynccontextmanager
    async def connection(self):
        if self._pool is None:
            yield self
        else:
            async with self._pool as client:
                yield client

    async def add_embedding(self, text: str) -> None:  # pragma: no cover - stub
        return None

    async def query_similar(
        self, query: str, k: int = 5
    ) -> List[str]:  # pragma: no cover - stub
        return []

    async def validate_runtime(self) -> ValidationResult:
        """Ensure the vector store can handle simple queries."""
        try:
            await self.query_similar("ping", k=1)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
