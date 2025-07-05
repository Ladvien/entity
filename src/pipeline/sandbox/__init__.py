"""Sandbox utilities for running and auditing contrib plugins."""

import warnings

from plugins.contrib.infrastructure.sandbox import DockerSandboxRunner, PluginAuditor

warnings.warn(
    "pipeline.sandbox is deprecated; use plugins.contrib.infrastructure.sandbox instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["PluginAuditor", "DockerSandboxRunner"]
