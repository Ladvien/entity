from __future__ import annotations

import warnings

warnings.warn(
    (
        "pipeline.cache.redis is deprecated; "
        "use plugins.contrib.resources.cache_backends.redis instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str):
    """Lazily import :class:`RedisCache` when requested."""

    if name == "RedisCache":
        from plugins.contrib.resources.cache_backends.redis import RedisCache

        return RedisCache
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["RedisCache"]  # noqa: F822
