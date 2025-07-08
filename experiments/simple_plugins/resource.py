from __future__ import annotations

"""Demonstration resource plugin, not production ready."""

from typing import Any, Dict, Protocol

from pipeline.base_plugins import ResourcePlugin


class StorageBackend(Protocol):
    async def add(self, item: Any) -> None: ...
    async def get_all(self) -> list[Any]: ...
    async def initialize(self) -> None: ...
    async def health_check(self) -> bool: ...
    def get_metrics(self) -> Dict[str, Any]: ...


class InMemoryBackend:
    """Simple in-memory backend implementing ``StorageBackend``."""

    def __init__(self) -> None:
        self.items: list[Any] = []

    async def add(self, item: Any) -> None:
        self.items.append(item)

    async def get_all(self) -> list[Any]:
        return list(self.items)

    async def initialize(self) -> None:
        return None

    async def health_check(self) -> bool:
        return True

    def get_metrics(self) -> Dict[str, Any]:
        return {"items": len(self.items)}


class ComposedResource(ResourcePlugin):
    """Resource plugin delegating behavior to a backend."""

    name = "composed_memory"

    def __init__(
        self, backend: StorageBackend | None = None, config: Dict | None = None
    ) -> None:
        super().__init__(config)
        self._backend: StorageBackend = backend or InMemoryBackend()

    async def initialize(self) -> None:
        await self._backend.initialize()

    async def health_check(self) -> bool:
        return await self._backend.health_check()

    def get_metrics(self) -> Dict[str, Any]:
        return self._backend.get_metrics()

    async def add_item(self, item: Any) -> None:
        await self._backend.add(item)

    async def items(self) -> list[Any]:
        return await self._backend.get_all()
