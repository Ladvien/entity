from __future__ import annotations

"""Pipeline-specific exception hierarchy."""

from typing import Optional


class PipelineError(Exception):
    """Base class for pipeline errors."""


class ResourceError(PipelineError):
    """Raised when a required resource is unavailable or fails."""


class ToolExecutionError(PipelineError):
    """Raised when execution of a tool fails."""

    def __init__(
        self, tool_name: str, original_exception: Optional[Exception] = None
    ) -> None:
        self.tool_name = tool_name
        self.original_exception = original_exception
        message = f"Tool '{tool_name}' execution failed"
        if original_exception:
            message += f": {original_exception}"
        super().__init__(message)
