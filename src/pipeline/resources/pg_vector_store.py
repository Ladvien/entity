from __future__ import annotations

from typing import Dict, List

import asyncpg
from pgvector import Vector
from pgvector.asyncpg import register_vector

from pipeline.resources.postgres import PostgresResource
from pipeline.resources.vectorstore import VectorStoreResource


class PgVectorStore(VectorStoreResource):
    """Postgres-backed vector store using pgvector."""

    name = "vector_memory"

    def __init__(
        self, config: Dict | None = None, database: PostgresResource | None = None
    ) -> None:
        super().__init__(config)
        self._table = self.config.get("table", "vector_memory")
        self._dim = int(self.config.get("dimensions", 3))
        self._db = database or PostgresResource(config)

    async def initialize(self) -> None:
        if self._db._pool is None:
            await self._db.initialize()
        await register_vector(self._db._pool)
        async with self._db.connection() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self._table} "
                f"(text TEXT, embedding VECTOR({self._dim}))"
            )

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        embedding = Vector(self._embed(text))
        if self._db._pool is None:
            await self._db.initialize()
        async with self._db.connection() as conn:
            await conn.execute(
                f"INSERT INTO {self._table} (text, embedding) VALUES ($1, $2)",
                text,
                embedding,
            )

    async def query_similar(self, query: str, k: int) -> List[str]:
        embedding = Vector(self._embed(query))
        if self._db._pool is None:
            await self._db.initialize()
        async with self._db.connection() as conn:
            rows = await conn.fetch(
                f"SELECT text FROM {self._table} ORDER BY embedding <-> $1 LIMIT $2",
                embedding,
                k,
            )
        return [row["text"] for row in rows]
