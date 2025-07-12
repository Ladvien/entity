from __future__ import annotations

from typing import Any, Dict, List

from entity.core.plugins import ResourcePlugin


class VectorStoreResource(ResourcePlugin):
    """Abstract vector store interface."""

    name = "vector_store"
    infrastructure_dependencies = ["vector_store"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def add_embedding(self, text: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def query_similar(
        self, query: str, k: int = 5
    ) -> List[str]:  # pragma: no cover - interface
        raise NotImplementedError
