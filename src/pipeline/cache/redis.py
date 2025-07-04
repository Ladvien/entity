from __future__ import annotations

import warnings

from user_plugins.resources.cache_backends.redis import RedisCache

warnings.warn(
    "pipeline.cache.redis is deprecated; use user_plugins.resources.cache_backends.redis instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["RedisCache"]
