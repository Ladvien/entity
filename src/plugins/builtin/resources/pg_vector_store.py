from __future__ import annotations

from typing import Any, Dict, List

from entity.core.plugins import ResourcePlugin, ValidationResult


class PgVectorStore(ResourcePlugin):
    """Placeholder pgvector-based store."""

    name = "pg_vector_store"
    infrastructure_dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._db: Any = None
        self.database: Any = None

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        self._db = self.database

    @classmethod
    def validate_dependencies(cls, registry: Any) -> "ValidationResult":
        if not registry.has_plugin("database"):
            return ValidationResult.error_result(
                "PgVectorStore requires the PostgresResource to be registered"
            )
        return ValidationResult.success_result()

    async def add_embedding(self, text: str) -> None:  # pragma: no cover - stub
        return None

    async def query_similar(self, query: str, k: int = 5) -> List[str]:  # noqa: D401
        return []
