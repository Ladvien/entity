from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """Dataclass for returning structured validation results."""

    success: bool
    errors: List[str] = field(default_factory=list)

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a success result."""
        return cls(success=True, errors=[])

    @classmethod
    def error(cls, error: str) -> "ValidationResult":
        """Create a failure result."""
        return cls(success=False, errors=[error])