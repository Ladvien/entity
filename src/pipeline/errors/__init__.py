from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from ..state import FailureInfo
from .context import (PipelineContextError, PluginContextError,
                      StageExecutionError)
from .exceptions import (PipelineError, PluginExecutionError, ResourceError,
                         ToolExecutionError)
from .models import ErrorResponse


@dataclass(slots=True)
class ErrorResponse:
    """Simple wrapper for error payloads."""

    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the payload as a plain dictionary."""
        return self.data.copy()


__all__ = [
    "ErrorResponse",
    "create_static_error_response",
    "create_error_response",
    "ErrorResponse",
    "PipelineError",
    "PluginExecutionError",
    "ResourceError",
    "ToolExecutionError",
    "PipelineContextError",
    "StageExecutionError",
    "PluginContextError",
    "ErrorResponse",
]


@dataclass(slots=True)
class ErrorResponse:
    """Structured error information returned to the caller."""

    error: str
    message: str | None = None
    error_id: str | None = None
    timestamp: str | None = None
    error_type: str | None = None
    stage: str | None = None
    plugin: str | None = None
    pipeline_id: str | None = None
    type: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain ``dict`` representation."""
        return {k: v for k, v in asdict(self).items() if v is not None}


# Generic fallback returned when even error handling fails
STATIC_ERROR_RESPONSE: Dict[str, Any] = {
    "error": "System error occurred",
    "message": "An unexpected error prevented processing your request.",
    "error_id": None,
    "timestamp": None,
    "type": "static_fallback",
}


def create_static_error_response(pipeline_id: str) -> ErrorResponse:
    """Return a copy of :data:`STATIC_ERROR_RESPONSE` populated with runtime info."""
    response = STATIC_ERROR_RESPONSE.copy()
    response["error_id"] = pipeline_id
    response["timestamp"] = datetime.now().isoformat()
    return ErrorResponse(response)


def create_error_response(pipeline_id: str, failure: FailureInfo) -> Dict[str, Any]:
    """Return a standardized error payload for ``failure``."""

    return {
        "error": failure.error_message,
        "error_type": failure.error_type,
        "stage": failure.stage,
        "plugin": failure.plugin_name,
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "type": "plugin_error",
    }
