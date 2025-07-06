from __future__ import annotations

import warnings

warnings.warn(
    (
        "pipeline.sandbox.audit is deprecated; "
        "use plugins.contrib.infrastructure.sandbox.audit instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str):
    if name == "PluginAuditor":
        from plugins.contrib.infrastructure.sandbox.audit import PluginAuditor

        return PluginAuditor
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PluginAuditor"]
