"""Abstract interface for key/value storage backends."""

from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import ResourcePlugin


class StorageResource(ResourcePlugin):

    infrastructure_dependencies = ["storage_backend"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    def get(
        self, key: str, default: Any | None = None
    ) -> Any:  # pragma: no cover - stub
        return default

    def set(self, key: str, value: Any) -> None:  # pragma: no cover - stub
        return None
