from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator

from entity.core.plugins import ResourcePlugin, ValidationResult


class DatabaseResource(ResourcePlugin):
    """Abstract database interface over a concrete backend."""

    infrastructure_dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:  # pragma: no cover - stub
        yield None

    async def validate_runtime(self) -> ValidationResult:
        """Verify the database connection is reachable."""
        try:
            async with self.connection():
                pass
        except Exception as exc:  # noqa: BLE001 - surface errors to caller
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
