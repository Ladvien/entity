"""Simple in-memory cache used in tests."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float | None


class InMemoryCache:
    """Minimal cache storing values in-process."""

    def __init__(self) -> None:
        self._data: Dict[str, _CacheEntry] = {}

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store ``value`` for ``key`` with optional ``ttl`` in seconds."""
        expires_at = time.monotonic() + ttl if ttl is not None else None
        self._data[key] = _CacheEntry(value, expires_at)

    def get(self, key: str) -> Any | None:
        """Return cached value if present and not expired."""
        entry = self._data.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at < time.monotonic():
            del self._data[key]
            return None
        return entry.value
