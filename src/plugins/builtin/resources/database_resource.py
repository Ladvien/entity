from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import ResourcePlugin


class DatabaseResource(ResourcePlugin):
    """Abstract database resource interface."""

    name = "database"
    infrastructure_dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def connection(self) -> Any:  # pragma: no cover - interface
        raise NotImplementedError
