# src/plugins/prompts/validation.py

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ValidationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """Represents a single validation issue"""

    level: ValidationLevel
    category: str
    message: str
    fix_suggestion: Optional[str] = None
    line_number: Optional[int] = None

    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.category}: {self.message}"


class ValidationResult(BaseModel):
    """Result of prompt validation"""

    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    errors: List[ValidationIssue] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_issue(
        self,
        level: ValidationLevel,
        category: str,
        message: str,
        fix_suggestion: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        """Add a validation issue"""
        issue = ValidationIssue(
            level=level,
            category=category,
            message=message,
            fix_suggestion=fix_suggestion,
            line_number=line_number,
        )

        self.issues.append(issue)

        if level in [ValidationLevel.WARNING]:
            self.warnings.append(issue)
        elif level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
            self.errors.append(issue)
            self.is_valid = False

    def add_error(
        self, category: str, message: str, fix_suggestion: Optional[str] = None
    ):
        """Convenience method to add an error"""
        self.add_issue(ValidationLevel.ERROR, category, message, fix_suggestion)

    def add_warning(
        self, category: str, message: str, fix_suggestion: Optional[str] = None
    ):
        """Convenience method to add a warning"""
        self.add_issue(ValidationLevel.WARNING, category, message, fix_suggestion)

    def add_info(self, category: str, message: str):
        """Convenience method to add info"""
        self.add_issue(ValidationLevel.INFO, category, message)

    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get a human-readable summary"""
        if self.is_valid and not self.warnings:
            return "✅ Validation passed with no issues"
        elif self.is_valid and self.warnings:
            return f"⚠️ Validation passed with {len(self.warnings)} warning(s)"
        else:
            return f"❌ Validation failed with {len(self.errors)} error(s) and {len(self.warnings)} warning(s)"
