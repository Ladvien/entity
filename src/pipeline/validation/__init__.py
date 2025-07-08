from __future__ import annotations

"""Pipeline component:   init  ."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of plugin validation operations."""

    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def success_result(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(True)

    @classmethod
    def error_result(cls, message: str) -> "ValidationResult":
        """Create a failed validation result with ``message``."""
        return cls(False, error_message=message)
