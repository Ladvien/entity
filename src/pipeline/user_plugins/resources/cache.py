from __future__ import annotations

"""Pipeline component: cache."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from user_plugins.resources.cache import CacheResource


def __getattr__(name: str) -> Any:
    if name == "CacheResource":
        from user_plugins.resources.cache import CacheResource

        return CacheResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["CacheResource"]
