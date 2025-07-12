"""Canonical storage resource."""

from __future__ import annotations

from typing import Any, Dict

from ..core.plugins import ValidationResult
from entity.config.models import StorageConfig
from pydantic import ValidationError


from .base import AgentResource


class Storage(AgentResource):
    """Simple key/value storage."""

    name = "storage"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._data: Dict[str, Any] = {}

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            StorageConfig.parse_obj(config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    async def validate_runtime(self) -> ValidationResult:
        """Check backend availability."""
        return ValidationResult.success_result()
