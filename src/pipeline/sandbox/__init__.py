<<<<<<< HEAD
"""Compatibility wrapper for sandbox utilities."""
=======
"""Sandbox utilities for running and auditing user_plugins."""
>>>>>>> af319b68dc2109eede14ae624413f7e5304d62df

import warnings

from user_plugins.infrastructure.sandbox import DockerSandboxRunner, PluginAuditor

warnings.warn(
    "pipeline.sandbox is deprecated; use user_plugins.infrastructure.sandbox instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["PluginAuditor", "DockerSandboxRunner"]
