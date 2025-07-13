"""Abstract interface for key/value storage backends."""

from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import ResourcePlugin, ValidationResult


class StorageResource(ResourcePlugin):

    infrastructure_dependencies = ["storage_backend"]
    resource_category = "filesystem"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    def get(
        self, key: str, default: Any | None = None
    ) -> Any:  # pragma: no cover - stub
        return default

    def set(self, key: str, value: Any) -> None:  # pragma: no cover - stub
        return None

    async def validate_runtime(self) -> ValidationResult:
        """Ensure the storage backend is accessible."""
        try:
            self.get("__ping__")
        except Exception as exc:  # noqa: BLE001 - propagate as validation error
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
