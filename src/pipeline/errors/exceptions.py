from __future__ import annotations

"""Pipeline-specific exception hierarchy."""

from typing import Optional


class PipelineError(Exception):
    """Base class for pipeline errors."""


class PluginExecutionError(PipelineError):
    """Raised when execution of a plugin fails."""

    def __init__(self, plugin_name: str, original_exception: Exception) -> None:
        self.plugin_name = plugin_name
        self.original_exception = original_exception
        super().__init__(f"{plugin_name} failed: {original_exception}")


class ResourceError(PipelineError):
    """Raised when a required resource is unavailable or fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ToolExecutionError(PipelineError):
    """Raised when execution of a tool fails."""

    def __init__(
        self,
        tool_name: str,
        original_exception: Optional[Exception] = None,
        result_key: str | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.original_exception = original_exception
        self.result_key = result_key
        message = f"Tool '{tool_name}' execution failed"
        if original_exception:
            message += f": {original_exception}"
        super().__init__(message)
