from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

from entity.core.plugins import ResourcePlugin


class DatabaseResource(ResourcePlugin):
    """Abstract database interface over a concrete backend."""

    infrastructure_dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:  # pragma: no cover - stub
        yield None

    def get_connection_pool(self) -> Any:  # pragma: no cover - stub
        """Return the underlying connection or pool."""
        return None
