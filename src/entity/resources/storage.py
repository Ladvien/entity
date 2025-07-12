"""Canonical storage resource."""

from __future__ import annotations

from typing import Any, Dict

from .interfaces.storage import StorageResource as StorageBackend

from .base import AgentResource


class Storage(AgentResource):
    """Simple key/value storage."""

    name = "storage"
    dependencies: list[str] = ["storage_backend"]

    def __init__(self, backend: StorageBackend, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.backend = backend

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self.backend.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.backend.set(key, value)
