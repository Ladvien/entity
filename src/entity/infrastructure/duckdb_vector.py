from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator, List
import math
import importlib

from entity.config.models import DuckDBConfig
from entity.plugins.base import ValidationResult
from entity.core.resources.container import PoolConfig, ResourcePool

from .vector_store import VectorStoreInfrastructure

try:
    duckdb = importlib.import_module("duckdb")
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    duckdb = None


class DuckDBVectorInfrastructure(VectorStoreInfrastructure):
    """Vector store backend using DuckDB."""

    name = "duckdb_vector_backend"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.path: str = self.config.get("path", ":memory:")
        self.table: str = self.config.get("table", "vector_mem")
        self._pool = ResourcePool(
            self._create_conn, PoolConfig(), "duckdb_vector_backend"
        )

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            DuckDBConfig(**config)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def initialize(self) -> None:
        if duckdb is None:
            raise RuntimeError("duckdb package not installed")
        await self._pool.initialize()
        async with self.connection() as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} (text TEXT, embedding DOUBLE[])"
            )
            self._maybe_commit(conn)

    def _create_conn(self) -> Any:
        if duckdb is None:
            raise RuntimeError("duckdb package not installed")
        return duckdb.connect(self.path)

    def get_connection_pool(self) -> ResourcePool:
        return self._pool

    def _maybe_commit(self, conn: Any) -> None:
        commit = getattr(conn, "commit", None)
        if callable(commit):
            commit()

    @asynccontextmanager
    async def connection(self) -> Iterator[Any]:
        conn = self._create_conn()
        try:
            yield conn
        finally:
            conn.close()

    def _embed(self, text: str) -> List[float]:
        return [float(ord(c)) for c in text][:256]

    async def add_embedding(self, text: str) -> None:
        async with self.connection() as conn:
            emb = self._embed(text)
            conn.execute(
                f"INSERT INTO {self.table} VALUES (?, ?)",
                (text, emb),
            )
            self._maybe_commit(conn)

    async def query_similar(self, query: str, k: int = 5) -> List[str]:
        async with self.connection() as conn:
            rows = conn.execute(f"SELECT text, embedding FROM {self.table}").fetchall()
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

        scored = sorted(((t, _distance(qvec, e)) for t, e in rows), key=lambda x: x[1])
        return [t for t, _ in scored[:k]]
