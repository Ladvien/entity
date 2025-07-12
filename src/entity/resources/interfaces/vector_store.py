from __future__ import annotations

from typing import Dict, List

from entity.core.plugins import ResourcePlugin, ValidationResult


class VectorStoreResource(ResourcePlugin):
    """Abstract vector store interface."""

    infrastructure_dependencies = ["vector_store"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def add_embedding(self, text: str) -> None:  # pragma: no cover - stub
        return None

    async def query_similar(
        self, query: str, k: int = 5
    ) -> List[str]:  # pragma: no cover - stub
        return []

    async def validate_runtime(self) -> ValidationResult:
        """Ensure the vector store can handle simple queries."""
        try:
            await self.query_similar("ping", k=1)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
