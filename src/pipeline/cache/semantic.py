from __future__ import annotations

import warnings
<<<<<<< HEAD
from typing import TYPE_CHECKING
=======
from typing import Any
>>>>>>> b74897eb07f4cc9a44a89de1546f06369e530ba2

warnings.warn(
    (
        "pipeline.cache.semantic is deprecated; "
        "use user_plugins.resources.cache_backends.semantic instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

if TYPE_CHECKING:  # pragma: no cover - for type checkers
    from plugins.contrib.resources.cache_backends.semantic import SemanticCache


def __getattr__(name: str):
    """Lazily import :class:`SemanticCache` when requested."""

    if name == "SemanticCache":
<<<<<<< HEAD
<<<<<<< HEAD
        from plugins.contrib.resources.cache_backends.semantic import \
            SemanticCache
=======
        from user_plugins.resources.cache_backends.semantic import SemanticCache
>>>>>>> da816a7a3dbe69257c5bbcbb38bb088649439bb0
=======
        from user_plugins.resources.cache_backends.semantic import \
            SemanticCache
>>>>>>> 9c565435c8c98d3dd664501aa929f40fe2e70c3f

        return SemanticCache
    raise AttributeError(f"module {__name__} has no attribute {name}")


<<<<<<< HEAD
<<<<<<< HEAD
if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from plugins.contrib.resources.cache_backends.semantic import SemanticCache

=======
SemanticCache: Any
>>>>>>> b74897eb07f4cc9a44a89de1546f06369e530ba2
__all__ = ["SemanticCache"]
=======
__all__ = ["SemanticCache"]  # noqa: F822
>>>>>>> 1b04dad19b0966409ec769baf967cf11db2e54fa
