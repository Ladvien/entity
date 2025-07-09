from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    valid: bool
    message: str | None = None

    @classmethod
    def success_result(cls) -> "ValidationResult":
        return cls(True)

    @classmethod
    def error_result(cls, message: str) -> "ValidationResult":
        return cls(False, message)


__all__ = ["ValidationResult"]
