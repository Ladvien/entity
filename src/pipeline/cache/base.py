from __future__ import annotations

"""Pipeline component: base."""

from abc import ABC, abstractmethod
from typing import Any


class CacheBackend(ABC):
    """Abstract caching backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Any:
        """Return value stored under ``key`` or ``None``."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` for ``key`` with optional ``ttl`` in seconds."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove ``key`` from the cache."""

    @abstractmethod
    async def clear(self) -> None:
        """Remove all cached values."""
