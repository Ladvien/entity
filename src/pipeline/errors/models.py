from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ErrorResponse:
    """Structure returned when a pipeline error occurs."""

    error: str
    message: Optional[str] = None
    error_type: Optional[str] = None
    stage: Optional[str] = None
    plugin: Optional[str] = None
    pipeline_id: Optional[str] = None
    error_id: Optional[str] = None
    timestamp: Optional[str] = None
    type: Optional[str] = None
