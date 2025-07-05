from __future__ import annotations

from typing import Any

from plugins.builtin.resources.vector_store import VectorStoreResource

from pipeline.cache.base import CacheBackend


class SemanticCache(CacheBackend):
    """Cache that retrieves values using vector similarity."""

    def __init__(self, store: VectorStoreResource, inner: CacheBackend) -> None:
        self.store = store
        self.inner = inner
        self._prompt_map: dict[str, str] = {}

    async def get(self, key: str) -> Any:
        return await self.inner.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.inner.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self.inner.delete(key)
        for prompt, mapped_key in list(self._prompt_map.items()):
            if mapped_key == key:
                del self._prompt_map[prompt]

    async def clear(self) -> None:
        await self.inner.clear()

    async def get_semantic(self, prompt: str) -> Any:
        similar = await self.store.query_similar(prompt, 1)
        if not similar:
            return None
        key = self._prompt_map.get(similar[0])
        if not key:
            return None
        return await self.inner.get(key)

    async def set_semantic(
        self, prompt: str, value: Any, ttl: int | None = None
    ) -> None:
        key = f"semantic:{len(self._prompt_map)}"
        self._prompt_map[prompt] = key
        await self.store.add_embedding(prompt)
        await self.inner.set(key, value, ttl)
