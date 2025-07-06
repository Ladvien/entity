from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

warnings.warn(
    (
        "pipeline.sandbox.audit is deprecated; "
        "use user_plugins.infrastructure.sandbox.audit instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from user_plugins.infrastructure.sandbox.audit import PluginAuditor


def __getattr__(name: str):
    if name == "PluginAuditor":
        from user_plugins.infrastructure.sandbox.audit import PluginAuditor

        return PluginAuditor
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PluginAuditor"]
