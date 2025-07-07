from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from ..state import FailureInfo
from .context import PipelineContextError, PluginContextError, StageExecutionError
from .exceptions import (
    PipelineError,
    PluginExecutionError,
    ResourceError,
    ToolExecutionError,
)
from .response import ErrorResponse

__all__ = [
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
]

# Generic fallback returned when even error handling fails
STATIC_ERROR_RESPONSE: Dict[str, Any] = {
    "error": "System error occurred",
    "message": "An unexpected error prevented processing your request.",
    "error_id": None,
    "timestamp": None,
    "type": "static_fallback",
}


def create_static_error_response(pipeline_id: str) -> ErrorResponse:
    """Return a generic :class:`ErrorResponse` populated with runtime info."""
    return ErrorResponse(
        error=STATIC_ERROR_RESPONSE["error"],
        message=STATIC_ERROR_RESPONSE["message"],
        error_id=pipeline_id,
        timestamp=datetime.now(),
        type=STATIC_ERROR_RESPONSE["type"],
    )


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
