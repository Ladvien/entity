from __future__ import annotations

"""Pipeline exceptions and reliability errors."""

from .errors import (
    PipelineError,
    PluginContextError,
    PluginExecutionError,
    ResourceError,
    ToolExecutionError,
    StageExecutionError,
    ErrorResponse,
    create_static_error_response,
)


class CircuitBreakerTripped(PipelineError):
    """Raised when a circuit breaker is open and execution is blocked."""


class MaxIterationsExceeded(PipelineError):
    """Raised when the pipeline runs more iterations than allowed."""


__all__ = [
    "PipelineError",
    "PluginContextError",
    "PluginExecutionError",
    "ResourceError",
    "ToolExecutionError",
    "StageExecutionError",
    "ErrorResponse",
    "create_static_error_response",
    "CircuitBreakerTripped",
    "MaxIterationsExceeded",
]
