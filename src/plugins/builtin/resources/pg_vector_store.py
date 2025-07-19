from __future__ import annotations

from typing import Any, Dict, List

from pgvector.asyncpg import register_vector, Vector

from entity.plugins.base import ValidationResult
from entity.resources.vector_store import VectorStoreResource


class PgVectorStore(VectorStoreResource):
    """Placeholder pgvector-based store."""

    name = "pg_vector_store"
    infrastructure_dependencies = ["database_backend"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._db: Any = None
        self.database: Any = None
        self._table = self.config.get("table", "vector_store")
        self._dim = int(self.config.get("dimensions", 256))

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    def _embed(self, text: str) -> Vector:
        values = [float(ord(c)) for c in text][: self._dim]
        if len(values) < self._dim:
            values.extend([0.0] * (self._dim - len(values)))
        return Vector(values)

    async def initialize(self) -> None:
        if self.database is None:
            return
        self._db = self.database
        async with self.database.connection() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await register_vector(conn)
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self._table} (text TEXT, embedding vector({self._dim}))"
            )

    @classmethod
    async def validate_dependencies(cls, registry: Any) -> "ValidationResult":
        if not registry.has_plugin("database"):
            return ValidationResult.error_result(
                "PgVectorStore requires the PostgresResource to be registered"
            )
        return ValidationResult.success_result()

    async def add_embedding(self, text: str) -> None:  # pragma: no cover - stub
        if self._db is None:
            return
        async with self._db.connection() as conn:
            await conn.execute(
                f"INSERT INTO {self._table} VALUES ($1, $2)",
                text,
                self._embed(text),
            )

    async def query_similar(self, query: str, k: int = 5) -> List[str]:  # noqa: D401
        if self._db is None:
            return []
        async with self._db.connection() as conn:
            rows = await conn.fetch(
                f"SELECT text FROM {self._table} ORDER BY embedding <-> $1 LIMIT $2",
                self._embed(query),
                k,
            )
        return [r["text"] for r in rows]
