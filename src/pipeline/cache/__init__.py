"""Caching utilities with pluggable backends."""

# Core backends
from .base import CacheBackend
from .memory import InMemoryCache

# Optional user-provided implementations
from .redis import RedisCache
from .semantic import SemanticCache

__all__ = ["CacheBackend", "InMemoryCache", "RedisCache", "SemanticCache"]
