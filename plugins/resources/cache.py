"""Compatibility shim for accessing :class:`CacheResource`."""

# Import the implementation from the user_plugins package to avoid recursion.
from pipeline.user_plugins.resources.cache import CacheResource

__all__ = ["CacheResource"]
