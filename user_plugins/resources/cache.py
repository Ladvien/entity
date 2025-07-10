"""Simple cache resource used in tests."""

from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import ResourcePlugin
from pipeline.cache import InMemoryCache


class CacheResource(ResourcePlugin):
    """Resource wrapper around :class:`InMemoryCache`."""

    name = "cache"
    stages: list = []

    def __init__(
        self, backend: InMemoryCache | None = None, config: Dict | None = None
    ) -> None:
        super().__init__(config or {})
        self.backend = backend or InMemoryCache()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def get_cached_result(self, name: str, params: Dict[str, Any]) -> Any | None:
        key = f"{name}:{sorted(params.items())}"
        return self.backend.get(key)

    async def cache_result(
        self, name: str, params: Dict[str, Any], result: Any, ttl: float | None = None
    ) -> None:
        key = f"{name}:{sorted(params.items())}"
        self.backend.set(key, result, ttl)
