"""Consolidated validation utilities for the Entity framework."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple

import yaml
from pydantic import BaseModel, ValidationError

from entity.plugins.validation import ValidationResult


class IdentifierValidator:
    """Validator for various types of identifiers."""

    SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    TABLE_NAME_PATTERN = re.compile(
        r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$"
    )

    PYTHON_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    ENV_VAR_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

    URL_SAFE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")

    @classmethod
    def validate_identifier(
        cls, identifier: str, pattern: Optional[Pattern] = None
    ) -> bool:
        """Validate an identifier against a pattern.

        Args:
            identifier: The identifier to validate
            pattern: Optional regex pattern to use (defaults to SAFE_IDENTIFIER_PATTERN)

        Returns:
            True if valid, False otherwise
        """
        if not identifier:
            return False

        if pattern is None:
            pattern = cls.SAFE_IDENTIFIER_PATTERN

        return bool(pattern.match(identifier))

    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """Validate a database table name."""
        return cls.validate_identifier(table_name, cls.TABLE_NAME_PATTERN)

    @classmethod
    def validate_column_name(cls, column_name: str) -> bool:
        """Validate a database column name."""
        return cls.validate_identifier(column_name, cls.SAFE_IDENTIFIER_PATTERN)

    @classmethod
    def validate_python_identifier(cls, identifier: str) -> bool:
        """Validate a Python identifier."""
        return cls.validate_identifier(identifier, cls.PYTHON_IDENTIFIER_PATTERN)

    @classmethod
    def validate_env_var(cls, var_name: str) -> bool:
        """Validate an environment variable name."""
        return cls.validate_identifier(var_name, cls.ENV_VAR_PATTERN)

    @classmethod
    def validate_url_safe(cls, identifier: str) -> bool:
        """Validate a URL-safe identifier."""
        return cls.validate_identifier(identifier, cls.URL_SAFE_PATTERN)


class SQLValidator:
    """Validator for SQL queries and components."""

    INJECTION_PATTERNS = [
        r";\s*(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)",
        r"--\s*",
        r"/\*.*\*/",
        r"\bUNION\b.*\bSELECT\b",
        r"\bEXEC\b|\bEXECUTE\b",
        r"xp_cmdshell",
        r"\bINTO\s+OUTFILE\b",
        r"\bLOAD_FILE\b",
        r"(0x[0-9a-fA-F]+|CHAR\([0-9]+\))",
        r"WAITFOR\s+DELAY",
        r"BENCHMARK\s*\(",
        r"pg_sleep",
    ]

    SAFE_FUNCTIONS = {
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
        "LENGTH",
        "LOWER",
        "UPPER",
        "TRIM",
        "SUBSTR",
        "SUBSTRING",
        "COALESCE",
        "CAST",
        "NOW",
        "DATE",
        "TIME",
        "YEAR",
        "MONTH",
        "DAY",
        "ABS",
        "ROUND",
        "FLOOR",
        "CEIL",
    }

    def __init__(self):
        """Initialize compiled patterns."""
        self._injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.INJECTION_PATTERNS
        ]

    def validate_query_safe(self, query: str) -> Tuple[bool, List[str]]:
        """Validate a SQL query for injection attempts.

        Args:
            query: The SQL query to validate

        Returns:
            Tuple of (is_safe, list_of_detected_patterns)
        """
        detected_patterns = []

        for pattern in self._injection_patterns:
            if pattern.search(query):
                detected_patterns.append(pattern.pattern)

        return len(detected_patterns) == 0, detected_patterns

    def validate_table_name(self, table_name: str) -> bool:
        """Validate a table name for SQL safety."""
        if not IdentifierValidator.validate_table_name(table_name):
            return False

        sql_keywords = {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "UNION",
        }
        if table_name.upper() in sql_keywords:
            return False

        return True

    def validate_column_names(self, column_names: List[str]) -> Tuple[bool, List[str]]:
        """Validate multiple column names.

        Args:
            column_names: List of column names to validate

        Returns:
            Tuple of (all_valid, list_of_invalid_names)
        """
        invalid_names = []

        for name in column_names:
            if not IdentifierValidator.validate_column_name(name):
                invalid_names.append(name)

        return len(invalid_names) == 0, invalid_names

    def sanitize_value(self, value: Any) -> str:
        """Sanitize a value for SQL insertion (for logging/display only).

        Note: Always use parameterized queries for actual SQL execution.
        """
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"


class JSONYAMLValidator:
    """Validator for JSON and YAML data."""

    @staticmethod
    def validate_json(data: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validate JSON string.

        Args:
            data: JSON string to validate

        Returns:
            Tuple of (is_valid, error_message, parsed_data)
        """
        try:
            parsed = json.loads(data)
            return True, None, parsed
        except json.JSONDecodeError as e:
            return False, str(e), None

    @staticmethod
    def validate_yaml(data: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validate YAML string.

        Args:
            data: YAML string to validate

        Returns:
            Tuple of (is_valid, error_message, parsed_data)
        """
        try:
            parsed = yaml.safe_load(data)
            return True, None, parsed
        except yaml.YAMLError as e:
            return False, str(e), None

    @staticmethod
    def validate_schema(data: Dict, schema_model: type[BaseModel]) -> ValidationResult:
        """Validate data against a Pydantic schema.

        Args:
            data: Dictionary to validate
            schema_model: Pydantic model class to validate against

        Returns:
            ValidationResult with success status and any errors
        """
        try:
            schema_model(**data)
            return ValidationResult.success()
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_path}: {error['msg']}")
            return ValidationResult(success=False, errors=errors)


class TypeValidator:
    """Validator for Python types and type hints."""

    @staticmethod
    def validate_type(value: Any, expected_type: type) -> bool:
        """Validate that a value matches expected type.

        Args:
            value: Value to check
            expected_type: Expected type

        Returns:
            True if type matches, False otherwise
        """
        return isinstance(value, expected_type)

    @staticmethod
    def validate_dict_schema(
        data: Dict, schema: Dict[str, type], allow_extra: bool = False
    ) -> Tuple[bool, List[str]]:
        """Validate dictionary against a simple type schema.

        Args:
            data: Dictionary to validate
            schema: Dictionary mapping keys to expected types
            allow_extra: Whether to allow extra keys not in schema

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        for key, expected_type in schema.items():
            if key not in data:
                errors.append(f"Missing required key: {key}")
            elif not isinstance(data[key], expected_type):
                actual_type = type(data[key]).__name__
                expected_name = expected_type.__name__
                errors.append(
                    f"Key '{key}' has wrong type: expected {expected_name}, got {actual_type}"
                )

        if not allow_extra:
            extra_keys = set(data.keys()) - set(schema.keys())
            for key in extra_keys:
                errors.append(f"Unexpected key: {key}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_list_types(data: List, expected_type: type) -> Tuple[bool, List[int]]:
        """Validate all items in a list are of expected type.

        Args:
            data: List to validate
            expected_type: Expected type for all items

        Returns:
            Tuple of (all_valid, list_of_invalid_indices)
        """
        invalid_indices = []

        for i, item in enumerate(data):
            if not isinstance(item, expected_type):
                invalid_indices.append(i)

        return len(invalid_indices) == 0, invalid_indices


class ValidationResultBuilder:
    """Builder for complex validation results."""

    def __init__(self):
        """Initialize the builder."""
        self._errors: List[str] = []
        self._warnings: List[str] = []
        self._context: Dict[str, Any] = {}

    def add_error(
        self, error: str, field: Optional[str] = None
    ) -> "ValidationResultBuilder":
        """Add an error to the result."""
        if field:
            self._errors.append(f"{field}: {error}")
        else:
            self._errors.append(error)
        return self

    def add_warning(
        self, warning: str, field: Optional[str] = None
    ) -> "ValidationResultBuilder":
        """Add a warning to the result."""
        if field:
            self._warnings.append(f"{field}: {warning}")
        else:
            self._warnings.append(warning)
        return self

    def add_context(self, key: str, value: Any) -> "ValidationResultBuilder":
        """Add context information to the result."""
        self._context[key] = value
        return self

    def merge(self, other_result: ValidationResult) -> "ValidationResultBuilder":
        """Merge another validation result into this builder."""
        if not other_result.success:
            self._errors.extend(other_result.errors)
        return self

    def build(self) -> ValidationResult:
        """Build the final validation result."""
        if self._errors:
            result = ValidationResult(success=False, errors=self._errors)
        else:
            result = ValidationResult.success()

        result.warnings = self._warnings
        result.context = self._context

        return result


def validate_email(email: str) -> bool:
    """Validate email address format."""
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(email_pattern.match(email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    url_pattern = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(url_pattern.match(url))


def validate_semantic_version(version: str) -> bool:
    """Validate semantic version format (e.g., 1.2.3)."""
    semver_pattern = re.compile(
        r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)?(?:\+[a-zA-Z0-9-]+)?$"
    )
    return bool(semver_pattern.match(version))
