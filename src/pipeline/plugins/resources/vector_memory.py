from __future__ import annotations

from typing import Dict, List, Optional

import asyncpg
from pgvector import Vector
from pgvector.asyncpg import register_vector

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class VectorMemoryResource(ResourcePlugin):
    """Postgres-backed vector memory using pgvector.

    Demonstrates **Preserve All Power (7)** by enabling advanced storage
    without changing the simple plugin API.
    """

    stages = [PipelineStage.PARSE]
    name = "vector_memory"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._connection: Optional[asyncpg.Connection] = None
        self._table = self.config.get("table", "vector_memory")
        self._dim = int(self.config.get("dimensions", 3))

    async def initialize(self) -> None:
        self._connection = await asyncpg.connect(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
        )
        await register_vector(self._connection)
        await self._connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await self._connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                text TEXT,
                embedding VECTOR({self._dim})
            )
            """
        )

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str) -> None:
        if self._connection is None:
            raise RuntimeError("Resource not initialized")
        embedding = Vector(self._embed(text))
        await self._connection.execute(
            f"INSERT INTO {self._table} (text, embedding) VALUES ($1, $2)",  # nosec B608
            text,
            embedding,
        )

    async def query_similar(self, text: str, k: int) -> List[str]:
        if self._connection is None:
            return []
        embedding = Vector(self._embed(text))
        rows = await self._connection.fetch(
            f"SELECT text FROM {self._table} ORDER BY embedding <-> $1 LIMIT $2",  # nosec B608
            embedding,
            k,
        )
        return [row["text"] for row in rows]
