"""Async Memory resource with truly asynchronous database operations."""

from __future__ import annotations

import asyncio
import fcntl
import json
from pathlib import Path
from typing import Any

from entity.resources.async_database import AsyncDatabaseResource
from entity.resources.exceptions import ResourceInitializationError
from entity.resources.vector_store import VectorStoreResource


class _InterProcessLock:
    """Async file-based lock for cross-process synchronization."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._file = None

    async def __aenter__(self) -> "_InterProcessLock":
        """Acquire the file lock asynchronously."""
        self._file = await asyncio.to_thread(open, self._path, "w")
        await asyncio.to_thread(fcntl.flock, self._file, fcntl.LOCK_EX)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Release the file lock asynchronously."""
        if self._file:
            await asyncio.to_thread(fcntl.flock, self._file, fcntl.LOCK_UN)
            self._file.close()
            self._file = None


class AsyncMemory:
    """Layer 3 canonical resource providing async persistent memory capabilities.

    This is the async version of the Memory class that uses truly asynchronous
    database operations instead of asyncio.to_thread() wrappers. It provides
    better performance and proper async patterns while maintaining the same
    interface and functionality.

    Key improvements:
    - Native async database operations (no thread pool usage)
    - Connection pooling for better performance
    - Query timeouts to prevent hanging operations
    - Better error handling and logging
    - Performance monitoring capabilities
    """

    def __init__(
        self,
        database: AsyncDatabaseResource | None,
        vector_store: VectorStoreResource | None,
    ) -> None:
        """Initialize AsyncMemory with async database and vector store resources.

        Args:
            database: Async database resource for structured data storage
            vector_store: Vector store resource for semantic search

        Raises:
            ResourceInitializationError: If database or vector_store is None
        """
        if database is None or vector_store is None:
            raise ResourceInitializationError(
                "AsyncDatabaseResource and VectorStoreResource are required"
            )
        self.database = database
        self.vector_store = vector_store
        self._lock = asyncio.Lock()

        # Setup inter-process locking if database has a file path
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
            True if both underlying resources are operational, False otherwise
        """
        return (
            self.database.health_check_sync() and self.vector_store.health_check_sync()
        )

    async def health_check_async(self) -> bool:
        """Async version of health check for better performance.

        Returns:
            True if both underlying resources are operational, False otherwise
        """
        # Run health checks concurrently for better performance
        db_healthy, vector_healthy = await asyncio.gather(
            self.database.health_check(),
            asyncio.to_thread(self.vector_store.health_check_sync),
            return_exceptions=True,
        )

        return db_healthy is True and vector_healthy is True

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check."""
        return self.health_check()

    def execute(self, query: str, *params: object) -> object:
        """Execute a raw database query synchronously (for compatibility).

        WARNING: This method should be avoided in async contexts.
        Use execute_async() instead.
        """
        return self.database.execute_sync(query, *params)

    async def execute_async(self, query: str, *params: object) -> Any:
        """Execute a raw database query asynchronously.

        Args:
            query: SQL query string to execute
            *params: Parameters to bind to the query

        Returns:
            Query result from the database

        Examples:
            >>> result = await memory.execute_async(
            ...     "SELECT * FROM conversations WHERE user_id = ?", "user123"
            ... )
        """
        return await self.database.execute(query, *params)

    def add_vector(self, table: str, vector: object) -> None:
        """Add a vector to the vector store.

        Args:
            table: Name of the table/collection to store the vector in
            vector: Vector data to store (typically embeddings)

        Examples:
            >>> memory.add_vector("embeddings", [0.1, 0.2, 0.3, ...])
        """
        self.vector_store.add_vector(table, vector)

    def query(self, query: str) -> object:
        """Execute a vector store query."""
        return self.vector_store.query(query)

    # ------------------------------------------------------------------
    # Persistent key-value storage helpers with async operations
    # ------------------------------------------------------------------

    async def _ensure_table(self) -> None:
        """Create the backing table if it doesn't exist.

        This method now uses native async database operations instead
        of asyncio.to_thread() wrappers.
        """
        if self._table_ready:
            return

        # Use native async database operation
        await self.database.execute(
            "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._table_ready = True

    async def _execute_with_locks(
        self, query: str, *params: Any, fetch_one: bool = False
    ) -> Any:
        """Execute a database query with appropriate locking.

        This method now uses native async database operations instead
        of asyncio.to_thread() wrappers, providing better performance
        and proper async patterns.
        """
        if self._process_lock is not None:
            async with self._process_lock:
                await self._ensure_table()
                async with self._lock:
                    if fetch_one:
                        return await self.database.execute_fetch_one(query, *params)
                    else:
                        return await self.database.execute(query, *params)
        else:
            async with self._lock:
                await self._ensure_table()
                if fetch_one:
                    return await self.database.execute_fetch_one(query, *params)
                else:
                    return await self.database.execute(query, *params)

    async def store(self, key: str, value: Any) -> None:
        """Persist value for key asynchronously with native async operations.

        Args:
            key: Storage key
            value: Value to store (will be JSON serialized)

        Examples:
            >>> await memory.store("user_preferences", {"theme": "dark"})
        """
        serialized = json.dumps(value)
        await self._execute_with_locks(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            key,
            serialized,
        )

    async def load(self, key: str, default: Any | None = None) -> Any:
        """Retrieve the stored value for key or default if missing.

        Args:
            key: Storage key to retrieve
            default: Default value if key is not found

        Returns:
            Stored value (JSON deserialized) or default

        Examples:
            >>> prefs = await memory.load("user_preferences", {})
            >>> theme = prefs.get("theme", "light")
        """
        row = await self._execute_with_locks(
            "SELECT value FROM memory WHERE key = ?",
            key,
            fetch_one=True,
        )
        if row is None:
            return default
        return json.loads(row[0])

    async def delete(self, key: str) -> bool:
        """Delete a key from memory storage.

        Args:
            key: Storage key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Examples:
            >>> deleted = await memory.delete("temp_data")
            >>> if deleted:
            ...     print("Temporary data cleared")
        """
        cursor = await self._execute_with_locks(
            "DELETE FROM memory WHERE key = ?",
            key,
        )
        # Check if any rows were affected
        return cursor.rowcount > 0 if hasattr(cursor, "rowcount") else True

    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory storage.

        Args:
            key: Storage key to check

        Returns:
            True if key exists, False otherwise

        Examples:
            >>> if await memory.exists("user_session"):
            ...     session = await memory.load("user_session")
        """
        row = await self._execute_with_locks(
            "SELECT 1 FROM memory WHERE key = ? LIMIT 1",
            key,
            fetch_one=True,
        )
        return row is not None

    async def keys(self, pattern: str | None = None) -> list[str]:
        """Get all keys in memory storage, optionally filtered by pattern.

        Args:
            pattern: Optional SQL LIKE pattern to filter keys

        Returns:
            List of keys matching the pattern

        Examples:
            >>> all_keys = await memory.keys()
            >>> user_keys = await memory.keys("user_%")
        """
        if pattern is None:
            cursor = await self._execute_with_locks("SELECT key FROM memory")
        else:
            cursor = await self._execute_with_locks(
                "SELECT key FROM memory WHERE key LIKE ?",
                pattern,
            )

        # Handle different cursor types
        if hasattr(cursor, "fetchall"):
            rows = await cursor.fetchall()
        else:
            rows = cursor

        return [row[0] for row in rows] if rows else []

    async def clear(self, pattern: str | None = None) -> int:
        """Clear keys from memory storage, optionally filtered by pattern.

        Args:
            pattern: Optional SQL LIKE pattern to filter keys to delete

        Returns:
            Number of keys deleted

        Examples:
            >>> # Clear all temporary data
            >>> count = await memory.clear("temp_%")
            >>> print(f"Cleared {count} temporary keys")
            >>>
            >>> # Clear everything
            >>> await memory.clear()
        """
        if pattern is None:
            cursor = await self._execute_with_locks("DELETE FROM memory")
        else:
            cursor = await self._execute_with_locks(
                "DELETE FROM memory WHERE key LIKE ?",
                pattern,
            )

        return cursor.rowcount if hasattr(cursor, "rowcount") else 0

    async def size(self) -> int:
        """Get the total number of keys in memory storage.

        Returns:
            Number of stored keys

        Examples:
            >>> count = await memory.size()
            >>> print(f"Memory contains {count} keys")
        """
        row = await self._execute_with_locks(
            "SELECT COUNT(*) FROM memory",
            fetch_one=True,
        )
        return row[0] if row else 0

    async def get_stats(self) -> dict[str, Any]:
        """Get memory and database statistics for monitoring.

        Returns:
            Dictionary with memory statistics

        Examples:
            >>> stats = await memory.get_stats()
            >>> print(f"Memory size: {stats['key_count']} keys")
            >>> print(f"DB connections: {stats['db_stats']['active_connections']}")
        """
        # Get memory statistics
        key_count = await self.size()

        # Get database connection statistics
        db_stats = await self.database.get_connection_stats()

        # Get health status
        health_status = await self.health_check_async()

        return {
            "key_count": key_count,
            "table_ready": self._table_ready,
            "has_process_lock": self._process_lock is not None,
            "health_status": health_status,
            "db_stats": db_stats,
        }

    async def batch_store(self, items: dict[str, Any]) -> None:
        """Store multiple key-value pairs in a single transaction.

        Args:
            items: Dictionary of key-value pairs to store

        Examples:
            >>> await memory.batch_store({
            ...     "user_1": {"name": "Alice", "age": 30},
            ...     "user_2": {"name": "Bob", "age": 25},
            ...     "config": {"version": "1.0", "debug": True}
            ... })
        """
        if not items:
            return

        # Prepare batch data
        batch_data = [(key, json.dumps(value)) for key, value in items.items()]

        # Execute batch insert with proper locking
        if self._process_lock is not None:
            async with self._process_lock:
                await self._ensure_table()
                async with self._lock:
                    await self.database.execute_many(
                        "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
                        batch_data,
                    )
        else:
            async with self._lock:
                await self._ensure_table()
                await self.database.execute_many(
                    "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
                    batch_data,
                )

    async def batch_load(self, keys: list[str]) -> dict[str, Any]:
        """Load multiple keys in a single query.

        Args:
            keys: List of keys to load

        Returns:
            Dictionary mapping keys to their values (missing keys are omitted)

        Examples:
            >>> values = await memory.batch_load(["user_1", "user_2", "config"])
            >>> print(f"Loaded {len(values)} out of 3 requested keys")
        """
        if not keys:
            return {}

        # Create parameterized query for multiple keys
        placeholders = ",".join("?" * len(keys))
        query = f"SELECT key, value FROM memory WHERE key IN ({placeholders})"

        cursor = await self._execute_with_locks(query, *keys)

        # Handle different cursor types
        if hasattr(cursor, "fetchall"):
            rows = await cursor.fetchall()
        else:
            rows = cursor

        # Build result dictionary
        result = {}
        for row in rows or []:
            key, value = row
            result[key] = json.loads(value)

        return result
