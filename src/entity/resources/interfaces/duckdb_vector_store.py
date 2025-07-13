from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator, List

from entity.pipeline.errors import ResourceInitializationError

try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    duckdb = None

from .vector_store import VectorStoreResource


class DuckDBVectorStore(VectorStoreResource):
    """Simple vector store using a DuckDB table."""

    name = "duckdb_vector_store"
    infrastructure_dependencies = ["database_backend"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.database: Any = None
        self._table = self.config.get("table", "vector_mem")
        self._pool = None

    def _maybe_commit(self, conn: Any) -> None:
        commit = getattr(conn, "commit", None)
        if callable(commit):
            commit()

    async def initialize(self) -> None:
        if duckdb is None:
            raise RuntimeError("duckdb package not installed")
        if self.database is None:
            raise ResourceInitializationError("Database backend not injected")
        self._pool = self.database.get_connection_pool()
        async with self.database.connection() as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {self._table} (text TEXT)")
            self._maybe_commit(conn)

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:
        if self.database is None:
            yield None
        else:
            async with self.database.connection() as conn:
                yield conn

    async def add_embedding(self, text: str) -> None:
        if self.database is None:
            return
        async with self.database.connection() as conn:
            conn.execute(f"INSERT INTO {self._table} VALUES (?)", (text,))
            self._maybe_commit(conn)

    async def query_similar(self, query: str, k: int = 5) -> List[str]:
        if self.database is None:
            return []
        async with self.database.connection() as conn:
            rows = conn.execute(
                f"SELECT text FROM {self._table} WHERE text LIKE ? LIMIT ?",
                (f"%{query}%", k),
            ).fetchall()
        return [row[0] for row in rows]


__all__ = ["DuckDBVectorStore"]
