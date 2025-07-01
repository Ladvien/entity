from __future__ import annotations

import asyncio
import json
import re
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

import aiosqlite

from .storage_backend import StorageBackend


class SQLiteStorage(StorageBackend):
    """SQLite based storage backend with a simple connection pool."""

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._path = str(self.config.get("path", ":memory:"))
        self._min_size = int(self.config.get("pool_min_size", 1))
        self._max_size = int(self.config.get("pool_max_size", 5))
        self._pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue()
        self._size = 0

    async def initialize(self) -> None:
        for _ in range(self._min_size):
            await self._add_conn()
        if self._history_table:
            async with self.connection() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table_name()} (
                        conversation_id TEXT,
                        role TEXT,
                        content TEXT,
                        metadata TEXT,
                        timestamp TEXT
                    )
                    """
                )
                await conn.commit()

    async def _add_conn(self) -> None:
        conn = await aiosqlite.connect(self._path)
        await self._pool.put(conn)
        self._size += 1

    async def acquire(self) -> aiosqlite.Connection:
        if self._pool.empty() and self._size < self._max_size:
            await self._add_conn()
        conn = await self._pool.get()
        return conn

    async def release(self, connection: aiosqlite.Connection) -> None:
        if self._pool.qsize() >= self._max_size:
            await connection.close()
            self._size -= 1
        else:
            await self._pool.put(connection)

    async def shutdown(self) -> None:
        while not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()
        self._size = 0

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiosqlite.Connection]:
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    def _convert_query(self, query: str) -> str:
        return re.sub(r"\$\d+", "?", query)

    async def execute(self, query: str, *args: Any) -> Any:
        async with self.connection() as conn:
            await conn.execute(self._convert_query(query), args)
            await conn.commit()

    async def fetch(self, query: str, *args: Any) -> Any:
        async with self.connection() as conn:
            cursor = await conn.execute(self._convert_query(query), args)
            rows = await cursor.fetchall()
            return rows

    async def fetchrow(self, query: str, *args: Any) -> Any:
        async with self.connection() as conn:
            cursor = await conn.execute(self._convert_query(query), args)
            row = await cursor.fetchone()
            return row

    async def fetchval(self, query: str, *args: Any) -> Any:
        row = await self.fetchrow(query, *args)
        return row[0] if row else None

    async def _do_health_check(self, connection: aiosqlite.Connection) -> None:
        await connection.execute("SELECT 1")
