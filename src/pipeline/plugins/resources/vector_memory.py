from __future__ import annotations

from typing import Dict, List, Optional

import asyncpg
from pgvector import Vector
from pgvector.asyncpg import register_vector

<<<<<<< HEAD
<<<<<<< HEAD
from pipeline.base_plugins import ValidationResult
from pipeline.stages import PipelineStage
from .postgres import ConnectionPoolResource, PostgresPoolResource
=======
from pipeline.plugins import ValidationResult
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
from pipeline.stages import PipelineStage

from .postgres import ConnectionPoolResource, PostgresPoolResource

<<<<<<< HEAD
class VectorMemoryResource(ConnectionPoolResource):
=======
from pipeline.plugins import ResourcePlugin
from pipeline.resources.memory import Memory
from pipeline.stages import PipelineStage


class VectorMemoryResource(ResourcePlugin, Memory):
>>>>>>> 66045f0cc3ea9a831e3ec579ceb40548cd673716
=======

class VectorMemoryResource(ConnectionPoolResource):
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
    """Postgres-backed vector memory using pgvector.

    Demonstrates **Preserve All Power (7)** by enabling advanced storage
    without changing the simple plugin API.
    """

    stages = [PipelineStage.PARSE]
    dependencies = ["database"]
    name = "vector_memory"

    @classmethod
    def validate_dependencies(cls, registry) -> ValidationResult:
        if not registry.has_plugin("database"):
            return ValidationResult.error_result("'database' resource is required")

        db_cls = registry._classes.get("database")
        if db_cls is None or not issubclass(db_cls, PostgresPoolResource):
            return ValidationResult.error_result(
                "database resource must support vector store (Postgres)"
            )
        return ValidationResult.success_result()

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[asyncpg.Pool] = None
        self._table = self.config.get("table", "vector_memory")
        self._dim = int(self.config.get("dimensions", 3))

    async def initialize(self) -> None:
        self._pool = await asyncpg.create_pool(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
        )
        await register_vector(self._pool)
        await self._pool.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await self._pool.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                text TEXT,
                embedding VECTOR({self._dim})
            )
            """
        )

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Optional[str] | None = None) -> str:
        raise NotImplementedError("VectorMemoryResource does not support get")

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError("VectorMemoryResource does not support set")

    def clear(self) -> None:
        raise NotImplementedError("VectorMemoryResource does not support clear")

    def _embed(self, text: str) -> List[float]:
        """Generate a naive embedding vector from ``text``."""

        embedding = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            embedding[i % self._dim] += float(byte)
        return [value / 255.0 for value in embedding]

    async def add_embedding(self, text: str) -> None:
<<<<<<< HEAD
<<<<<<< HEAD
        if self._pool is None:
=======
        """Store an embedding for ``text`` in the backing database."""

        if self._connection is None:
>>>>>>> 5254d8c570961a7008f230d11e4766175159d40a
=======
        if self._pool is None:
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
            raise RuntimeError("Resource not initialized")
        embedding = Vector(self._embed(text))
        await self._pool.execute(
            f"INSERT INTO {self._table} (text, embedding) VALUES ($1, $2)",  # nosec B608
            text,
            embedding,
        )

<<<<<<< HEAD
    async def query_similar(self, text: str, k: int) -> List[str]:
        if self._pool is None:
<<<<<<< HEAD
=======
    async def query_similar(self, text: str, top_k: int) -> List[str]:
        """Return ``top_k`` texts most similar to ``text``."""

        if self._connection is None:
>>>>>>> 5254d8c570961a7008f230d11e4766175159d40a
=======
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
            return []
        embedding = Vector(self._embed(text))
        rows = await self._pool.fetch(
            f"SELECT text FROM {self._table} ORDER BY embedding <-> $1 LIMIT $2",  # nosec B608
            embedding,
            top_k,
        )
        return [row["text"] for row in rows]

    async def shutdown(self) -> None:
        await super().shutdown()
