from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


class PipelineError(Exception):
    """Base class for pipeline exceptions."""


class PluginContextError(PipelineError):
    pass


class PluginExecutionError(PipelineError):
    def __init__(self, plugin_name: str, original_exception: Exception) -> None:
        super().__init__(str(original_exception))
        self.plugin_name = plugin_name
        self.original_exception = original_exception


class ResourceError(PipelineError):
    pass


class ToolExecutionError(PipelineError):
    pass


class StageExecutionError(PipelineError):
    pass


@dataclass
class ErrorResponse:
    error: str
    message: str
    error_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    type: str = "error"

    def to_dict(self) -> dict:
        return {
            "error": self.error,
            "message": self.message,
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "type": self.type,
        }


def create_static_error_response(pipeline_id: str) -> ErrorResponse:
    return ErrorResponse(
        error="System error occurred",
        message="An unexpected error prevented processing your request.",
        error_id=pipeline_id,
        type="static_fallback",
    )


__all__ = [
    "PipelineError",
    "PluginContextError",
    "PluginExecutionError",
    "ResourceError",
    "StageExecutionError",
    "ToolExecutionError",
    "ErrorResponse",
    "create_static_error_response",
]
