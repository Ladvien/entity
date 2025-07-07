from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Dict

from ..state import FailureInfo
from .context import (PipelineContextError, PluginContextError,
                      StageExecutionError)
from .exceptions import (PipelineError, PluginExecutionError, ResourceError,
                         ToolExecutionError)
from .models import ErrorResponse

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
    "ErrorResponse",
]

# Generic fallback returned when even error handling fails
STATIC_ERROR_RESPONSE = ErrorResponse(
    error="System error occurred",
    message="An unexpected error prevented processing your request.",
    type="static_fallback",
)


def create_static_error_response(pipeline_id: str) -> ErrorResponse:
    """Return a copy of :data:`STATIC_ERROR_RESPONSE` populated with runtime info."""
    return replace(
        STATIC_ERROR_RESPONSE,
        error_id=pipeline_id,
        timestamp=datetime.now().isoformat(),
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
