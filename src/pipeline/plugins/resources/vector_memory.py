from __future__ import annotations

from typing import Dict, List, Optional

import asyncpg
from asyncpg.utils import _quote_ident
from pgvector import Vector
from pgvector.asyncpg import register_vector

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class VectorMemoryResource(ResourcePlugin):
    """Postgres-backed vector memory using pgvector.

    Required configuration matches standard database connection details. The
    ``table`` and ``dimensions`` options control where embeddings are stored
    and the size of each vector.
    """

    stages = [PipelineStage.PARSE]
    name = "vector_memory"

    def __init__(self, config: Dict | None = None) -> None:
        """Persist initialization parameters for later use."""

        super().__init__(config)
        self._connection: Optional[asyncpg.Connection] = None
        self._table = self.config.get("table", "vector_memory")
        self._dim = int(self.config.get("dimensions", 3))

    def _quoted_table(self) -> str:
        return _quote_ident(self._table)

    async def initialize(self) -> None:
        """Connect to Postgres and create the embedding table if needed."""

        self._connection = await asyncpg.connect(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
        )
        await register_vector(self._connection)
        await self._connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        table = self._quoted_table()
        query = f"""
            CREATE TABLE IF NOT EXISTS {table} (
                text TEXT,
                embedding VECTOR({self._dim})
            )
        """
        await self._connection.execute(query)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str) -> None:
        """Store ``text`` along with its generated embedding."""

        if self._connection is None:
            raise RuntimeError("Resource not initialized")
        embedding = Vector(self._embed(text))
        table = self._quoted_table()
        await self._connection.execute(
            f"INSERT INTO {table} (text, embedding) VALUES ($1, $2)",
            text,
            embedding,
        )

    async def query_similar(self, text: str, k: int) -> List[str]:
        """Return the ``k`` most similar stored texts to ``text``."""

        if self._connection is None:
            return []
        embedding = Vector(self._embed(text))
        table = self._quoted_table()
        rows = await self._connection.fetch(
            f"SELECT text FROM {table} ORDER BY embedding <-> $1 LIMIT $2",
            embedding,
            k,
        )
        return [row["text"] for row in rows]
