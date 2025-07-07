"""Compatibility wrapper for the Redis cache backend.

This module re-exports :class:`RedisCache` from the community plugins so
user configuration can continue referencing
``user_plugins.resources.cache_backends.redis:RedisCache`` without
duplicating its implementation.
"""

from plugins.contrib.resources.cache_backends.redis import RedisCache

__all__ = ["RedisCache"]
