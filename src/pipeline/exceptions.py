"""Custom exceptions used across the pipeline."""

from __future__ import annotations


class PluginError(Exception):
    """Base class for plugin related errors."""


class PluginExecutionError(PluginError):
    """Exception raised when a plugin fails during execution.

    Args:
        plugin_name: Name of the plugin that failed.
        original_exception: The underlying exception that triggered this error.
    """

    def __init__(self, plugin_name: str, original_exception: Exception) -> None:
        self.plugin_name = plugin_name
        self.original_exception = original_exception
        super().__init__(str(original_exception))


class CircuitBreakerTripped(PluginError):
    """Raised when repeated plugin failures prevent execution.

    Args:
        plugin_name: Name of the plugin whose circuit breaker tripped.
    """

    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Circuit breaker tripped for {plugin_name}")
