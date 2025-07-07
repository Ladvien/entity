from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
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

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary excluding ``None`` values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
