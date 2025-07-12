from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from entity.core.state import FailureInfo
from pipeline.stages import PipelineStage


class PipelineError(Exception):
    """Base class for pipeline exceptions."""


class PluginContextError(PipelineError):
    """Raised when plugin preconditions fail."""

    def __init__(
        self,
        stage: "PipelineStage",
        plugin_name: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.plugin_name = plugin_name
        self.context = context or {}


class PluginExecutionError(PipelineError):
    def __init__(self, plugin_name: str, original_exception: Exception) -> None:
        super().__init__(str(original_exception))
        self.plugin_name = plugin_name
        self.original_exception = original_exception


class ResourceError(PipelineError):
    pass


class ResourceInitializationError(ResourceError):
    """Raised when a resource is missing required dependencies."""


class ToolExecutionError(PipelineError):
    pass


class StageExecutionError(PipelineError):
    """Raised when an error occurs while executing a pipeline stage."""

    def __init__(
        self,
        stage: "PipelineStage",
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.context = context or {}


@dataclass
class ErrorResponse:
    """Standard structure returned when a plugin fails."""

    error: str
    message: str
    error_id: str | None = None
    plugin: str | None = None
    stage: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    type: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.error,
            "message": self.message,
            "error_id": self.error_id,
            "plugin": self.plugin,
            "stage": self.stage,
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


def create_error_response(pipeline_id: str, info: FailureInfo) -> ErrorResponse:
    """Return an error response populated with plugin failure details."""

    return ErrorResponse(
        error=info.error_message,
        message="Unable to process request",
        error_id=pipeline_id,
        plugin=info.plugin_name,
        stage=info.stage,
        type="plugin_error",
    )


__all__ = [
    "PipelineError",
    "PluginContextError",
    "PluginExecutionError",
    "ResourceError",
    "ResourceInitializationError",
    "StageExecutionError",
    "ToolExecutionError",
    "ErrorResponse",
    "create_static_error_response",
    "create_error_response",
]
