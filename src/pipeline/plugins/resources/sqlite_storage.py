from __future__ import annotations

<<<<<<< HEAD
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
=======
import json
from datetime import datetime
from typing import Dict, List, Optional

import aiosqlite

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.resources.storage import StorageBackend
from pipeline.stages import PipelineStage


class SQLiteStorageResource(ResourcePlugin, StorageBackend):
    """SQLite-based conversation history storage."""

    stages = [PipelineStage.PARSE]
    name = "storage"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._path = self.config.get("path", ":memory:")
        self._table = self.config.get("history_table", "chat_history")
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {self._table} (
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                metadata TEXT,
                timestamp REAL
            )"""
        )
        await self._conn.commit()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._conn is None:
            return
        for entry in history:
            await self._conn.execute(
                f"INSERT INTO {self._table} (conversation_id, role, content, metadata, timestamp)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp.timestamp(),
                ),
            )
        await self._conn.commit()

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        if self._conn is None:
            return []
        cursor = await self._conn.execute(
            f"SELECT role, content, metadata, timestamp FROM {self._table} "
            "WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        history: List[ConversationEntry] = []
        for role, content, metadata, ts in rows:
            metadata_dict = json.loads(metadata) if metadata else {}
            history.append(
                ConversationEntry(
                    content=content,
                    role=role,
                    metadata=metadata_dict,
                    timestamp=datetime.fromtimestamp(ts),
                )
            )
        return history

    async def shutdown(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
>>>>>>> a2fde49ed50a219b934336428d39351655a5f9c5
