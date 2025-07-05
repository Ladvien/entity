"""Caching utilities with pluggable backends."""

from .base import CacheBackend
from .memory import InMemoryCache


def get_redis_cache() -> type[CacheBackend]:
    """Return the :class:`RedisCache` class with a lazy import."""

    from plugins.contrib.resources.cache_backends.redis import RedisCache

    return RedisCache


def get_semantic_cache() -> type[CacheBackend]:
    """Return the :class:`SemanticCache` class with a lazy import."""

    from plugins.contrib.resources.cache_backends.semantic import SemanticCache

    return SemanticCache


__all__ = [
    "CacheBackend",
    "InMemoryCache",
    "get_redis_cache",
    "get_semantic_cache",
]
