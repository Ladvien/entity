from __future__ import annotations

from typing import Dict, List, Optional

import asyncpg
from pgvector import Vector
from pgvector.asyncpg import register_vector

from pipeline.plugins.resources.postgres_database import PostgresDatabaseResource
from pipeline.plugins.resources.postgres_pool import PostgresConnectionPool
from pipeline.resources.vectorstore import VectorStoreResource


class PgVectorStore(VectorStoreResource):
    """Postgres-backed vector store using pgvector."""

    name = "vector_memory"

    def __init__(
        self,
        config: Dict | None = None,
        connection: PostgresDatabaseResource | PostgresConnectionPool | None = None,
    ) -> None:
        super().__init__(config)
        self._table = self.config.get("table", "vector_memory")
        self._dim = int(self.config.get("dimensions", 3))
        self._external = connection
        self._connection: Optional[asyncpg.Connection] = None
        self._pool: Optional[PostgresConnectionPool] = None
        if isinstance(connection, PostgresConnectionPool):
            self._pool = connection
        elif isinstance(connection, PostgresDatabaseResource):
            self._connection = connection._connection

    async def initialize(self) -> None:
        if self._pool is not None:
            if self._pool._pool is None:
                await self._pool.initialize()
            await register_vector(self._pool._pool)
            async with self._pool.connection() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {self._table} "
                    f"(text TEXT, embedding VECTOR({self._dim}))"
                )
            return

        if self._connection is None:
            self._pool = await asyncpg.create_pool(
                database=str(self.config.get("name")),
                host=str(self.config.get("host", "localhost")),
                port=int(self.config.get("port", 5432)),
                user=str(self.config.get("username")),
                password=str(self.config.get("password")),
                min_size=int(self.config.get("pool_min_size", 1)),
                max_size=int(self.config.get("pool_max_size", 5)),
            )
            await register_vector(self._pool)
            async with self._pool.connection() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {self._table} "
                    f"(text TEXT, embedding VECTOR({self._dim}))"
                )
            return

        await register_vector(self._connection)
        await self._connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await self._connection.execute(
            f"CREATE TABLE IF NOT EXISTS {self._table} (text TEXT, embedding VECTOR({self._dim}))"
        )

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        embedding = Vector(self._embed(text))
        if self._pool is not None:
            async with self._pool.connection() as conn:
                await conn.execute(
                    f"INSERT INTO {self._table} (text, embedding) VALUES ($1, $2)",
                    text,
                    embedding,
                )
            return
        if self._connection is None:
            raise RuntimeError("Resource not initialized")
        await self._connection.execute(
            f"INSERT INTO {self._table} (text, embedding) VALUES ($1, $2)",
            text,
            embedding,
        )

    async def query_similar(self, query: str, k: int) -> List[str]:
        embedding = Vector(self._embed(query))
        if self._pool is not None:
            async with self._pool.connection() as conn:
                rows = await conn.fetch(
                    f"SELECT text FROM {self._table} ORDER BY embedding <-> $1 LIMIT $2",
                    embedding,
                    k,
                )
            return [row["text"] for row in rows]
        if self._connection is None:
            return []
        rows = await self._connection.fetch(
            f"SELECT text FROM {self._table} ORDER BY embedding <-> $1 LIMIT $2",
            embedding,
            k,
        )
        return [row["text"] for row in rows]
