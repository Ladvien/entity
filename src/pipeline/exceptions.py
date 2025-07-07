from __future__ import annotations

"""Compatibility exceptions for pipeline modules."""

from .errors import (
    PipelineError,
    PluginExecutionError,
    ResourceError,
    ToolExecutionError,
)


class CircuitBreakerTripped(PipelineError):
    """Raised when repeated plugin failures prevent execution."""

    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Circuit breaker tripped for {plugin_name}")


class MaxIterationsExceeded(PipelineError):
    """Raised when the pipeline exceeds the configured iteration limit."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"Maximum iterations of {limit} exceeded")


__all__ = [
    "PipelineError",
    "PluginExecutionError",
    "ToolExecutionError",
    "ResourceError",
    "CircuitBreakerTripped",
    "MaxIterationsExceeded",
]
