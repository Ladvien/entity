from __future__ import annotations

import warnings

<<<<<<< HEAD
from plugins.resources.vectorstore import VectorStoreResource
=======
from user_plugins.resources.cache_backends.semantic import SemanticCache
>>>>>>> 1e2dac3d1112a41dbbaee20650efe1189d1883ea

warnings.warn(
    (
        "pipeline.cache.semantic is deprecated; "
        "use user_plugins.resources.cache_backends.semantic instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["SemanticCache"]
