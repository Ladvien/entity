from __future__ import annotations

import warnings

warnings.warn(
    (
        "pipeline.cache.semantic is deprecated; "
        "use plugins.contrib.resources.cache_backends.semantic instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str):
    """Lazily import :class:`SemanticCache` when requested."""

    if name == "SemanticCache":
        from plugins.contrib.resources.cache_backends.semantic import SemanticCache

        return SemanticCache
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["SemanticCache"]
