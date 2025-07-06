"""Sandbox utilities for running and auditing contrib plugins."""

import warnings

warnings.warn(
    "pipeline.sandbox is deprecated; use plugins.contrib.infrastructure.sandbox instead",
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str):
    if name == "DockerSandboxRunner":
        from plugins.contrib.infrastructure.sandbox.runner import DockerSandboxRunner

        return DockerSandboxRunner
    if name == "PluginAuditor":
        from plugins.contrib.infrastructure.sandbox.audit import PluginAuditor

        return PluginAuditor
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PluginAuditor", "DockerSandboxRunner"]
