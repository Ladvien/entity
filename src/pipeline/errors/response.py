from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ErrorResponse:
    """Serialized representation of an error."""

    error: str
    message: str
    error_id: str | None = None
    timestamp: str | None = None
    type: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of this error."""
        return {
            "error": self.error,
            "message": self.message,
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "type": self.type,
        }


__all__ = ["ErrorResponse"]
