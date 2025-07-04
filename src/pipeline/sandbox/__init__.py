"""Compatibility wrapper for sandbox utilities."""

import warnings

from user_plugins.infrastructure.sandbox import DockerSandboxRunner, PluginAuditor

warnings.warn(
    "pipeline.sandbox is deprecated; use user_plugins.infrastructure.sandbox instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["PluginAuditor", "DockerSandboxRunner"]
