"""Custom exceptions used across the pipeline."""

from __future__ import annotations


class PluginError(Exception):
    """Base class for plugin related errors."""


class PluginExecutionError(PluginError):
<<<<<<< HEAD
    """Exception raised when a plugin fails during execution."""
=======
    """Exception raised when a plugin fails during execution.

    Args:
        plugin_name: Name of the plugin that failed.
        original_exception: The underlying exception that triggered this error.
    """
>>>>>>> 4dbf3a92c50743e827fc62272eb07044f1bb4653

    def __init__(self, plugin_name: str, original_exception: Exception) -> None:
        self.plugin_name = plugin_name
        self.original_exception = original_exception
        super().__init__(str(original_exception))


class CircuitBreakerTripped(PluginError):
<<<<<<< HEAD
    """Raised when repeated plugin failures prevent execution."""
=======
    """Raised when repeated plugin failures prevent execution.

    Args:
        plugin_name: Name of the plugin whose circuit breaker tripped.
    """
>>>>>>> 4dbf3a92c50743e827fc62272eb07044f1bb4653

    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Circuit breaker tripped for {plugin_name}")
