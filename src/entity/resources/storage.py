from __future__ import annotations

"""Canonical storage resource."""

from typing import Any, Dict

from .base import AgentResource


class Storage(AgentResource):
    """Simple key/value storage."""

    name = "storage"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._data: Dict[str, Any] = {}

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
