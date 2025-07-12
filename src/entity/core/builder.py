from __future__ import annotations

"""Deprecated builder module."""

import warnings
from typing import Any

__all__ = ["_AgentBuilder"]

warnings.warn(
    "'entity.core.builder' is deprecated. Use 'Agent' methods instead.",
    DeprecationWarning,
    stacklevel=2,
)


def _AgentBuilder(*args: Any, **kwargs: Any):
    from .agent import _AgentBuilder as Builder

    return Builder(*args, **kwargs)
