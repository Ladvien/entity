from __future__ import annotations

"""Backward compatibility wrapper for the moved ResourceContainer."""

from entity.core.resources.container import PoolConfig, ResourceContainer, ResourcePool

__all__ = ["ResourceContainer", "ResourcePool", "PoolConfig"]
