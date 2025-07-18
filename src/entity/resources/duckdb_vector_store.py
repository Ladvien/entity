from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator, List
import math

from entity.pipeline.errors import ResourceInitializationError

try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    duckdb = None

from .vector_store import VectorStoreResource


class DuckDBVectorStore(VectorStoreResource):
    """Simple vector store using a DuckDB table.

    This implementation stores text alongside a naive numeric embedding and
    performs similarity search using cosine distance. The embedding is derived
    from the UTF-8 code points of the text and is only intended as a minimal
    placeholder for real embeddings.
    """

    name = "duckdb_vector_store"
    infrastructure_dependencies = ["database_backend"]
    resource_category = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.database_backend: Any = None
        self._table = self.config.get("table", "vector_mem")
        self._pool = None

    # ------------------------------------------------------------------
    # Compatibility layer
    # ------------------------------------------------------------------
    @property
    def database(self) -> Any:
        """Backward compatible accessor for the database backend."""

        return self.database_backend

    @database.setter
    def database(self, value: Any) -> None:
        self.database_backend = value

    def _embed(self, text: str) -> List[float]:
        """Return a simple numeric embedding for ``text``."""
        return [float(ord(c)) for c in text][:256]

    def _maybe_commit(self, conn: Any) -> None:
        commit = getattr(conn, "commit", None)
        if callable(commit):
            commit()

    async def initialize(self) -> None:
        if duckdb is None:
            raise RuntimeError("duckdb package not installed")
        if self.database_backend is None:
            raise ResourceInitializationError(
                "Database backend not injected", self.name
            )
        self._pool = self.database_backend.get_connection_pool()
        async with self.database_backend.connection() as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self._table} (text TEXT, embedding DOUBLE[])"
            )
            self._maybe_commit(conn)

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:
        if self.database_backend is None:
            yield None
        else:
            async with self.database_backend.connection() as conn:
                yield conn

    async def add_embedding(self, text: str) -> None:
        if self.database_backend is None:
            return
        async with self.database_backend.connection() as conn:
            emb = self._embed(text)
            conn.execute(
                f"INSERT INTO {self._table} VALUES (?, ?)",
                (text, emb),
            )
            self._maybe_commit(conn)

    async def query_similar(self, query: str, k: int = 5) -> List[str]:
        if self.database_backend is None:
            return []
        async with self.database_backend.connection() as conn:
            rows = conn.execute(f"SELECT text, embedding FROM {self._table}").fetchall()
        if not rows:
            return []
        qvec = self._embed(query)

        def _distance(a: List[float], b: List[float]) -> float:
            size = min(len(a), len(b))
            if size == 0:
                return float("inf")
            dot = sum(a[i] * b[i] for i in range(size))
            na = math.sqrt(sum(a[i] * a[i] for i in range(size)))
            nb = math.sqrt(sum(b[i] * b[i] for i in range(size)))
            return 1 - dot / (na * nb) if na and nb else float("inf")

        scored = sorted(
            ((text, _distance(qvec, emb)) for text, emb in rows),
            key=lambda x: x[1],
        )
        return [text for text, _ in scored[:k]]


__all__ = ["DuckDBVectorStore"]
