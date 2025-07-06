from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

warnings.warn(
    (
        "pipeline.cache.semantic is deprecated; "
        "use plugins.contrib.resources.cache_backends.semantic instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

if TYPE_CHECKING:  # pragma: no cover - for type checkers
    from plugins.contrib.resources.cache_backends.semantic import SemanticCache


def __getattr__(name: str):
    """Lazily import :class:`SemanticCache` when requested."""

    if name == "SemanticCache":
        from plugins.contrib.resources.cache_backends.semantic import \
            SemanticCache

        return SemanticCache
    raise AttributeError(f"module {__name__} has no attribute {name}")


<<<<<<< HEAD
if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from plugins.contrib.resources.cache_backends.semantic import SemanticCache

__all__ = ["SemanticCache"]
=======
__all__ = ["SemanticCache"]  # noqa: F822
>>>>>>> 1b04dad19b0966409ec769baf967cf11db2e54fa
