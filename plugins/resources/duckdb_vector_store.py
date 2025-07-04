from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import duckdb

from plugins.resources.duckdb_database import DuckDBDatabaseResource
from plugins.resources.vector_store import VectorStoreResource


class DuckDBVectorStore(VectorStoreResource):
    """Simple DuckDB-backed vector store."""

    name = "vector_memory"

    def __init__(
        self,
        config: Dict | None = None,
        connection: DuckDBDatabaseResource | None = None,
    ) -> None:
        super().__init__(config)
        self._table = self.config.get("table", "vector_memory")
        self._dim = int(self.config.get("dimensions", 3))
        self._external = connection
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        if isinstance(connection, DuckDBDatabaseResource):
            self._connection = connection._connection

    async def initialize(self) -> None:
        if self._connection is None:
            self._connection = await asyncio.to_thread(
                duckdb.connect, self.config.get("path", ":memory:")
            )
        await asyncio.to_thread(
            self._connection.execute,
            f"CREATE TABLE IF NOT EXISTS {self._table} (text TEXT, embedding DOUBLE[{self._dim}])",
        )

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        embedding = self._embed(text)
        if self._connection is None:
            raise RuntimeError("Resource not initialized")
        await asyncio.to_thread(
            self._connection.execute,
            f"INSERT INTO {self._table} (text, embedding) VALUES (?, ?)",
            [text, embedding],
        )

    async def query_similar(self, query: str, k: int) -> List[str]:
        embedding = self._embed(query)
        if self._connection is None:
            return []
        query = (
            f"SELECT text FROM {self._table} "
            "ORDER BY list_cosine_similarity(embedding, ?) DESC LIMIT ?"
        )
        rel = await asyncio.to_thread(
            self._connection.execute,
            query,
            [embedding, k],
        )
        rows = await asyncio.to_thread(rel.fetchall)
        return [row[0] for row in rows]

    async def shutdown(self) -> None:
        if self._connection is not None and not self._external:
            await asyncio.to_thread(self._connection.close)
            self._connection = None
