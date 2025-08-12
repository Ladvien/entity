from __future__ import annotations

import asyncio
import fcntl
import json
from pathlib import Path
from typing import Any


class _InterProcessLock:
    """Simple file-based lock for cross-process synchronization."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._file = None

    async def __aenter__(self) -> "_InterProcessLock":
        self._file = await asyncio.to_thread(open, self._path, "w")
        await asyncio.to_thread(fcntl.flock, self._file, fcntl.LOCK_EX)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._file:
            await asyncio.to_thread(fcntl.flock, self._file, fcntl.LOCK_UN)
            self._file.close()
            self._file = None


from entity.resources.database import DatabaseResource
from entity.resources.exceptions import ResourceInitializationError
from entity.resources.vector_store import VectorStoreResource


class Memory:
    """Layer 3 canonical resource providing persistent memory capabilities.

    Memory is one of the four canonical resources guaranteed to be available to
    every workflow. It provides both structured (database) and semantic (vector)
    storage with automatic user isolation and cross-process synchronization.

    This class follows the 4-layer architecture:
    - Layer 3: Canonical Agent Resources (Memory)
    - Depends on Layer 2: Resource Interfaces (DatabaseResource, VectorStoreResource)

    Attributes:
        database: The underlying database resource for structured data.
        vector_store: The underlying vector store for semantic search.

    Examples:
        >>> from entity.resources import Memory, DatabaseResource, VectorStoreResource
        >>> from entity.infrastructure import DuckDBInfrastructure
        >>>
        >>> duckdb = DuckDBInfrastructure("./agent_memory.duckdb")
        >>> db_resource = DatabaseResource(duckdb)
        >>> vector_resource = VectorStoreResource(duckdb)
        >>> memory = Memory(db_resource, vector_resource)
    """

    def __init__(
        self,
        database: DatabaseResource | None,
        vector_store: VectorStoreResource | None,
    ) -> None:
        """Initialize Memory with database and vector store resources.

        Args:
            database: Database resource for structured data storage.
            vector_store: Vector store resource for semantic search.

        Raises:
            ResourceInitializationError: If database or vector_store is None.
        """

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
        """Check if both database and vector store are healthy.

        Returns:
            True if both underlying resources are operational, False otherwise.
        """

        return (
            self.database.health_check_sync() and self.vector_store.health_check_sync()
        )

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check.

        Returns:
            True if both underlying resources are operational, False otherwise.
        """
        return self.health_check()

    def execute(self, query: str, *params: object) -> object:
        """Execute a raw database query.

        Args:
            query: SQL query string to execute.
            *params: Parameters to bind to the query.

        Returns:
            Query result from the database.

        Examples:
            >>> result = memory.execute("SELECT * FROM conversations WHERE user_id = ?", "user123")
        """

        return self.database.execute(query, *params)

    def add_vector(self, table: str, vector: object) -> None:
        """Add a vector to the vector store.

        Args:
            table: Name of the table/collection to store the vector in.
            vector: Vector data to store (typically embeddings).

        Examples:
            >>> memory.add_vector("embeddings", [0.1, 0.2, 0.3, ...])
        """

        self.vector_store.add_vector(table, vector)

    def query(self, query: str) -> object:
        """Execute a vector store query."""

        return self.vector_store.query(query)

    async def _ensure_table(self) -> None:
        """Create the backing table if it doesn't exist."""

        if self._table_ready:
            return
        await asyncio.to_thread(
            self.database.execute,
            "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)",
        )
        self._table_ready = True

    async def _execute_with_locks(
        self, query: str, *params: Any, fetch_one: bool = False
    ) -> Any:
        """Execute a database query with appropriate locking."""
        if self._process_lock is not None:
            async with self._process_lock:
                await self._ensure_table()
                async with self._lock:
                    result = await asyncio.to_thread(
                        self.database.execute,
                        query,
                        *params,
                    )
                    if fetch_one:
                        return result.fetchone() if result else None
                    return result
        else:
            async with self._lock:
                await self._ensure_table()
                result = await asyncio.to_thread(
                    self.database.execute,
                    query,
                    *params,
                )
                if fetch_one:
                    return result.fetchone() if result else None
                return result

    async def store(self, key: str, value: Any) -> None:
        """Persist ``value`` for ``key`` asynchronously."""

        serialized = json.dumps(value)
        await self._execute_with_locks(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            key,
            serialized,
        )

    async def load(self, key: str, default: Any | None = None) -> Any:
        """Retrieve the stored value for ``key`` or ``default`` if missing."""
        row = await self._execute_with_locks(
            "SELECT value FROM memory WHERE key = ?",
            key,
            fetch_one=True,
        )
        if row is None:
            return default
        return json.loads(row[0])
