from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from .base import CacheBackend


class InMemoryCache(CacheBackend):
    """Simple in-memory cache with optional TTL support."""

    def __init__(self, default_ttl: int | None = None) -> None:
        self._store: Dict[str, Tuple[Any, float | None]] = {}
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires = item
        if expires and expires < time.time():
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expire_at = None
        ttl = ttl if ttl is not None else self._default_ttl
        if ttl:
            expire_at = time.time() + ttl
        self._store[key] = (value, expire_at)

    async def clear(self) -> None:
        self._store.clear()
