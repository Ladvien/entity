"""Sandbox utilities for running and auditing user_plugins."""

from .audit import PluginAuditor

try:  # optional dependency
    from .runner import DockerSandboxRunner
except Exception:  # pragma: no cover - missing docker or cdktf
    DockerSandboxRunner = None  # type: ignore

__all__ = ["PluginAuditor", "DockerSandboxRunner"]
