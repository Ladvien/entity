from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.contrib.resources.cache import CacheResource


def __getattr__(name: str):
    if name == "CacheResource":
        from plugins.contrib.resources.cache import CacheResource

        return CacheResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["CacheResource"]
