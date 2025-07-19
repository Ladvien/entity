"""Canonical storage resource."""

from __future__ import annotations

from typing import Any, Dict

from ..core.plugins import ResourcePlugin, ValidationResult
from entity.config.models import StorageConfig
from entity.core.validation import validate_model


from .base import AgentResource


class StorageResource(ResourcePlugin):
    """Abstract interface for key/value storage backends."""

    infrastructure_dependencies = ["file_system"]
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


class Storage(AgentResource):
    """Simple key/value storage."""

    name = "storage"
    resource_category = "filesystem"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._data: Dict[str, Any] = {}

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        return validate_model(StorageConfig, config)

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    async def validate_runtime(self) -> ValidationResult:
        """Check backend availability."""
        return ValidationResult.success_result()

    async def health_check(self) -> bool:
        """Simple check that storage dictionary is accessible."""
        try:
            _ = len(self._data)
            return True
        except Exception:  # noqa: BLE001
            return False
