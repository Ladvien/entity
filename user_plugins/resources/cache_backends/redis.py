"""Compatibility wrapper for the Redis cache backend.

This module re-exports :class:`RedisCache` from the community plugins so
user configuration can continue referencing
``user_plugins.resources.cache_backends.redis:RedisCache`` without
duplicating its implementation.
"""


class RedisCache:
    """Placeholder for the optional Redis cache backend."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - example
        raise NotImplementedError("Redis backend not available")


__all__ = ["RedisCache"]
