from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass(slots=True)
class ErrorResponse:
    """Standard structure for pipeline errors."""

    error: str
    message: str
    error_id: str | None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    type: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error,
            "message": self.message,
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
        }
