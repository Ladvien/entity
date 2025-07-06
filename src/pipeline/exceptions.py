from __future__ import annotations

"""Compatibility exceptions for pipeline modules."""

from .errors import (PipelineError, PluginExecutionError, ResourceError,
                     ToolExecutionError)


class CircuitBreakerTripped(PipelineError):
    """Raised when repeated plugin failures prevent execution."""

    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Circuit breaker tripped for {plugin_name}")


__all__ = [
    "PipelineError",
    "PluginExecutionError",
    "ToolExecutionError",
    "ResourceError",
    "CircuitBreakerTripped",
]
