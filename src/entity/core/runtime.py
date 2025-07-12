from __future__ import annotations

"""Deprecated runtime module."""

import warnings

from .agent import _AgentRuntime as AgentRuntime

__all__ = ["AgentRuntime"]

warnings.warn(
    "'entity.core.runtime' is deprecated. Use 'Agent' methods instead.",
    DeprecationWarning,
    stacklevel=2,
)
