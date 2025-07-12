from __future__ import annotations

from typing import Any, Dict

from entity.resources.interfaces.database import DatabaseResource
from entity.core.plugins import ValidationResult


class DuckDBResource(DatabaseResource):
    """Database interface wired to DuckDB infrastructure."""

    dependencies = ["database_infra"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return ValidationResult.success_result()

    @classmethod
    def validate_dependencies(cls, registry: Any) -> ValidationResult:
        return ValidationResult.success_result()
