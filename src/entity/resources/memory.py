from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import fcntl


class _InterProcessLock:
    """Simple file-based lock for cross-process synchronization."""

    def __init__(self, path: str) -> None:
        self._file = open(path, "w")

    async def __aenter__(self) -> "_InterProcessLock":
        await asyncio.to_thread(fcntl.flock, self._file, fcntl.LOCK_EX)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await asyncio.to_thread(fcntl.flock, self._file, fcntl.LOCK_UN)


from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.resources.exceptions import ResourceInitializationError


class Memory:
    """Layer 3 resource that exposes persistent memory capabilities."""

    def __init__(
        self,
        database: DatabaseResource | None,
        vector_store: VectorStoreResource | None,
    ) -> None:
        """Create the memory wrapper with required resources."""

        if database is None or vector_store is None:
            raise ResourceInitializationError(
                "DatabaseResource and VectorStoreResource are required"
            )
        self.database = database
        self.vector_store = vector_store
        self._lock = asyncio.Lock()
        db_path = getattr(self.database.infrastructure, "file_path", None)
        lock_file = (
            Path(str(db_path)).with_suffix(".lock") if db_path is not None else None
        )
        self._process_lock = (
            _InterProcessLock(str(lock_file)) if lock_file is not None else None
        )
        self._table_ready = False

    def health_check(self) -> bool:
        """Return ``True`` if both underlying resources are healthy."""

        return self.database.health_check() and self.vector_store.health_check()

    def execute(self, query: str, *params: object) -> object:
        """Execute a database query."""

        return self.database.execute(query, *params)

    def add_vector(self, table: str, vector: object) -> None:
        """Store a vector via the underlying vector resource."""

        self.vector_store.add_vector(table, vector)

    def query(self, query: str) -> object:
        """Execute a vector store query."""

        return self.vector_store.query(query)

    # ------------------------------------------------------------------
    # Persistent key-value storage helpers
    # ------------------------------------------------------------------

    async def _ensure_table(self) -> None:
        """Create the backing table if it doesn't exist."""

        if self._table_ready:
            return
        await asyncio.to_thread(
            self.database.execute,
            "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)",
        )
        self._table_ready = True

    async def store(self, key: str, value: Any) -> None:
        """Persist ``value`` for ``key`` asynchronously."""

        serialized = json.dumps(value)
        if self._process_lock is not None:
            async with self._process_lock:
                await self._ensure_table()
                async with self._lock:
                    await asyncio.to_thread(
                        self.database.execute,
                        "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
                        key,
                        serialized,
                    )
        else:
            async with self._lock:
                await self._ensure_table()
                await asyncio.to_thread(
                    self.database.execute,
                    "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
                    key,
                    serialized,
                )

    async def load(self, key: str, default: Any | None = None) -> Any:
        """Retrieve the stored value for ``key`` or ``default`` if missing."""
        if self._process_lock is not None:
            async with self._process_lock:
                await self._ensure_table()
                async with self._lock:
                    relation = await asyncio.to_thread(
                        self.database.execute,
                        "SELECT value FROM memory WHERE key = ?",
                        key,
                    )
                    row = relation.fetchone()
        else:
            async with self._lock:
                await self._ensure_table()
                relation = await asyncio.to_thread(
                    self.database.execute,
                    "SELECT value FROM memory WHERE key = ?",
                    key,
                )
                row = relation.fetchone()
        if row is None:
            return default
        return json.loads(row[0])
