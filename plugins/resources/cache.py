<<<<<< codex/review-modules-and-add-docstrings
"""Simple caching resource."""

from plugins.resources.cache import CacheResource
======
"""Compatibility shim for accessing :class:`CacheResource`."""

# Import the implementation from the user_plugins package to avoid recursion.
from pipeline.user_plugins.resources.cache import CacheResource
>>>>>> main

__all__ = ["CacheResource"]
