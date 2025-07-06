from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

warnings.warn(
    (
        "pipeline.cache.semantic is deprecated; "
        "use user_plugins.resources.cache_backends.semantic instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

<<<<<< codex/update-test-imports-and-verify-pytest-setup
if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.contrib.resources.cache_backends.semantic import SemanticCache
=======
if TYPE_CHECKING:  # pragma: no cover - for type checkers
    from user_plugins.resources.cache_backends.semantic import SemanticCache
>>>>>> main


def __getattr__(name: str):
    """Lazily import :class:`SemanticCache` when requested."""

    if name == "SemanticCache":
        from user_plugins.resources.cache_backends.semantic import SemanticCache

        return SemanticCache
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["SemanticCache"]  # noqa: F822 - imported dynamically
