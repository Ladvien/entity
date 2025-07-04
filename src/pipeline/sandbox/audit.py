from __future__ import annotations

import warnings

from user_plugins.infrastructure.sandbox.audit import PluginAuditor

warnings.warn(
    "pipeline.sandbox.audit is deprecated; use user_plugins.infrastructure.sandbox.audit instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["PluginAuditor"]
