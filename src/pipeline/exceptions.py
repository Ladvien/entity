from __future__ import annotations

from .errors import (
    PipelineError,
    PluginContextError,
    PluginExecutionError,
    ResourceError,
    StageExecutionError,
    ToolExecutionError,
)


class CircuitBreakerTripped(PipelineError):
    """Raised when a circuit breaker blocks execution."""


class MaxIterationsExceeded(PipelineError):
    """Raised when a pipeline exceeds the iteration limit."""


__all__ = [
    "PipelineError",
    "PluginContextError",
    "PluginExecutionError",
    "ResourceError",
    "StageExecutionError",
    "ToolExecutionError",
    "CircuitBreakerTripped",
    "MaxIterationsExceeded",
]
