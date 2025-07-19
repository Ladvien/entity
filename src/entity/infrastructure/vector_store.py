from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Iterator

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool


class VectorStoreInfrastructure(InfrastructurePlugin):
    """Base class for vector store backends."""

    infrastructure_type = "vector_store"
    resource_category = "database"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def add_embedding(self, text: str) -> None:  # pragma: no cover - stub
        return None

    async def query_similar(
        self, query: str, k: int = 5
    ) -> List[str]:  # pragma: no cover - stub
        return []

    def get_connection_pool(self) -> ResourcePool:
        return ResourcePool(lambda: None, PoolConfig())

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:  # pragma: no cover - stub
        yield None

    async def validate_runtime(self, breaker: Any | None = None) -> ValidationResult:
        try:
            await self.query_similar("ping", 1)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
