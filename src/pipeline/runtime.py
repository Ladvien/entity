"""Deprecated shim exposing :class:`AgentRuntime`.

Import :class:`entity.core.runtime.AgentRuntime` or use ``entity.Agent``
instead. This module will be removed in a future release.
"""

from entity.core.runtime import AgentRuntime

__all__ = ["AgentRuntime"]
