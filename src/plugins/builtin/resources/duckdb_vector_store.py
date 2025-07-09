from __future__ import annotations

"""DuckDB-backed vector store resource."""
import asyncio
import re
from typing import Dict, List, Optional

import duckdb

from pipeline.exceptions import ResourceError
from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource
from plugins.builtin.resources.vector_store import VectorStoreResource


class DuckDBVectorStore(VectorStoreResource):
    """Simple DuckDB-backed vector store."""

    name = "vector_memory"

    dependencies = ["database"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        table = self.config.get("table", "vector_memory")
        self._table = self._sanitize_identifier(table)
        self._dim = int(self.config.get("dimensions", 3))
        self.database: DuckDBDatabaseResource | None = None
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._external = False

    @staticmethod
    def _sanitize_identifier(name: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid identifier: {name}")
        return name

    async def initialize(self) -> None:
        if self.database and self.database._connection is not None:
            self._connection = self.database._connection
            self._external = True
        if self._connection is None:
            self._connection = await asyncio.to_thread(
                duckdb.connect, self.config.get("path", ":memory:")
            )
        await asyncio.to_thread(
            self._connection.execute,
            f"CREATE TABLE IF NOT EXISTS {self._table} (text TEXT, embedding DOUBLE[{self._dim}])",
        )  # nosec B608
        # table name sanitized

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        embedding = self._embed(text)
        if self._connection is None:
            raise ResourceError("Resource not initialized")
        await asyncio.to_thread(
            self._connection.execute,
            f"INSERT INTO {self._table} (text, embedding) VALUES (?, ?)",  # nosec
            [text, embedding],
        )

    async def query_similar(self, query: str, k: int) -> List[str]:
        embedding = self._embed(query)
        if self._connection is None:
            return []
        query = (
            f"SELECT text FROM {self._table} "
            "ORDER BY list_cosine_similarity(embedding, ?) DESC LIMIT ?"  # nosec
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
