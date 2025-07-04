from __future__ import annotations

import warnings

from user_plugins.resources.cache_backends.semantic import SemanticCache

warnings.warn(
    (
        "pipeline.cache.semantic is deprecated; "
        "use user_plugins.resources.cache_backends.semantic instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["SemanticCache"]
