from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

# Generic fallback returned when even error handling fails
STATIC_ERROR_RESPONSE: Dict[str, Any] = {
    "error": "System error occurred",
    "message": "An unexpected error prevented processing your request.",
    "error_id": None,
    "timestamp": None,
    "type": "static_fallback",
}


def create_static_error_response(pipeline_id: str) -> Dict[str, Any]:
    """Return a copy of :data:`STATIC_ERROR_RESPONSE` populated with runtime info."""
    response = STATIC_ERROR_RESPONSE.copy()
    response["error_id"] = pipeline_id
    response["timestamp"] = datetime.now().isoformat()
    return response
