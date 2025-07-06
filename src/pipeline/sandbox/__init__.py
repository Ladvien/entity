"""Sandbox utilities for running and auditing contrib plugins."""

import warnings
from typing import TYPE_CHECKING

warnings.warn(
    "pipeline.sandbox is deprecated; use user_plugins.infrastructure.sandbox instead",
    DeprecationWarning,
    stacklevel=2,
)

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from user_plugins.infrastructure.sandbox.audit import PluginAuditor
    from user_plugins.infrastructure.sandbox.runner import DockerSandboxRunner


def __getattr__(name: str):
    if name == "DockerSandboxRunner":
        from user_plugins.infrastructure.sandbox.runner import \
            DockerSandboxRunner

        return DockerSandboxRunner
    if name == "PluginAuditor":
        from user_plugins.infrastructure.sandbox.audit import PluginAuditor

        return PluginAuditor
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PluginAuditor", "DockerSandboxRunner"]
