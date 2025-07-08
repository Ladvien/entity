from __future__ import annotations

"""Built-in plugins and resources."""

from typing import Any

import redis.asyncio as redis

from pipeline.cache.base import CacheBackend


class RedisCache(CacheBackend):
    """Redis-based cache backend."""

    def __init__(
        self, url: str = "redis://localhost:6379/0", default_ttl: int | None = None
    ) -> None:
        self._client = redis.from_url(url)
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any:
        value = await self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def clear(self) -> None:
        await self._client.flushdb()
