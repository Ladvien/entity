from __future__ import annotations

import warnings

from plugins.contrib.infrastructure.sandbox.audit import PluginAuditor

warnings.warn(
    (
        "pipeline.sandbox.audit is deprecated; "
        "use plugins.contrib.infrastructure.sandbox.audit instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["PluginAuditor"]
