from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

warnings.warn(
    (
        "pipeline.cache.redis is deprecated; use "
        "user_plugins.resources.cache_backends.redis instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)


if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from user_plugins.resources.cache_backends.redis import RedisCache


def __getattr__(name: str):
    """Lazily import :class:`RedisCache` when requested."""

    if name == "RedisCache":
        from user_plugins.resources.cache_backends.redis import RedisCache

        return RedisCache
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["RedisCache"]
