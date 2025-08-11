"""Memory component architecture using decorator pattern for composable features."""

from __future__ import annotations

import asyncio
import json
from abc import ABC
from typing import Any, List, Optional, Protocol

from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource


class IMemory(Protocol):
    """Protocol defining the interface for all memory implementations.

    This protocol ensures all memory implementations and decorators
    provide a consistent interface for memory operations.
    """

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with the given key.

        Args:
            key: The key to store the value under
            value: The value to store (must be JSON serializable)
            user_id: Optional user ID for user-scoped storage
        """
        ...

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value by key.

        Args:
            key: The key to load
            default: Default value if key doesn't exist
            user_id: Optional user ID for user-scoped storage

        Returns:
            The stored value or default if not found
        """
        ...

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key from memory.

        Args:
            key: The key to delete
            user_id: Optional user ID for user-scoped storage

        Returns:
            True if deleted, False if key didn't exist
        """
        ...

    async def exists(self, key: str, user_id: Optional[str] = None) -> bool:
        """Check if a key exists in memory.

        Args:
            key: The key to check
            user_id: Optional user ID for user-scoped storage

        Returns:
            True if key exists, False otherwise
        """
        ...

    async def keys(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[str]:
        """Get all keys matching an optional pattern.

        Args:
            pattern: Optional glob pattern to filter keys
            user_id: Optional user ID for user-scoped storage

        Returns:
            List of matching keys
        """
        ...

    async def clear(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> int:
        """Clear all keys matching an optional pattern.

        Args:
            pattern: Optional glob pattern to filter keys
            user_id: Optional user ID for user-scoped storage

        Returns:
            Number of keys deleted
        """
        ...

    async def size(self, user_id: Optional[str] = None) -> int:
        """Get the number of keys in memory.

        Args:
            user_id: Optional user ID for user-scoped storage

        Returns:
            Number of keys
        """
        ...

    def health_check(self) -> bool:
        """Check if the memory system is healthy.

        Returns:
            True if healthy, False otherwise
        """
        ...


class BaseMemory:
    """Base memory implementation using database and vector store.

    This provides the core memory functionality that can be enhanced
    with decorators for additional features like TTL, LRU, locking, etc.
    """

    def __init__(
        self,
        database: DatabaseResource,
        vector_store: VectorStoreResource,
        table_name: str = "entity_memory",
    ):
        """Initialize base memory.

        Args:
            database: Database resource for structured storage
            vector_store: Vector store resource for semantic search
            table_name: Name of the database table to use
        """
        self.database = database
        self.vector_store = vector_store
        self.table_name = table_name
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _ensure_initialized(self) -> None:
        """Ensure the memory table is created."""
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            await self._ensure_table()
            self._initialized = True

    async def _ensure_table(self) -> None:
        """Create the memory table if it doesn't exist."""
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await asyncio.to_thread(self.database.execute, create_table_query)

        # Create index for user_id
        create_index_query = f"""
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id
        ON {self.table_name}(user_id);
        """
        await asyncio.to_thread(self.database.execute, create_index_query)

    def _make_key(self, key: str, user_id: Optional[str] = None) -> str:
        """Create a scoped key for user isolation."""
        if user_id:
            return f"{user_id}:{key}"
        return key

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with the given key."""
        await self._ensure_initialized()

        scoped_key = self._make_key(key, user_id)
        serialized = json.dumps(value)

        query = f"""
        INSERT OR REPLACE INTO {self.table_name} (key, value, user_id, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        await asyncio.to_thread(
            self.database.execute, query, scoped_key, serialized, user_id
        )

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value by key."""
        await self._ensure_initialized()

        scoped_key = self._make_key(key, user_id)

        query = f"SELECT value FROM {self.table_name} WHERE key = ?"
        result = await asyncio.to_thread(self.database.execute, query, scoped_key)

        if result and len(result) > 0:
            return json.loads(result[0][0])
        return default

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key from memory."""
        await self._ensure_initialized()

        scoped_key = self._make_key(key, user_id)

        query = f"DELETE FROM {self.table_name} WHERE key = ?"
        await asyncio.to_thread(self.database.execute, query, scoped_key)

        # Check if any rows were affected
        changes_query = "SELECT changes()"
        changes = await asyncio.to_thread(self.database.execute, changes_query)
        return changes[0][0] > 0 if changes else False

    async def exists(self, key: str, user_id: Optional[str] = None) -> bool:
        """Check if a key exists in memory."""
        await self._ensure_initialized()

        scoped_key = self._make_key(key, user_id)

        query = f"SELECT 1 FROM {self.table_name} WHERE key = ? LIMIT 1"
        result = await asyncio.to_thread(self.database.execute, query, scoped_key)

        return bool(result and len(result) > 0)

    async def keys(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[str]:
        """Get all keys matching an optional pattern."""
        await self._ensure_initialized()

        if user_id:
            if pattern:
                query = f"SELECT key FROM {self.table_name} WHERE user_id = ? AND key GLOB ?"
                glob_pattern = f"{user_id}:{pattern}"
                result = await asyncio.to_thread(
                    self.database.execute, query, user_id, glob_pattern
                )
            else:
                query = f"SELECT key FROM {self.table_name} WHERE user_id = ?"
                result = await asyncio.to_thread(self.database.execute, query, user_id)
        else:
            if pattern:
                query = f"SELECT key FROM {self.table_name} WHERE key GLOB ?"
                result = await asyncio.to_thread(self.database.execute, query, pattern)
            else:
                query = f"SELECT key FROM {self.table_name}"
                result = await asyncio.to_thread(self.database.execute, query)

        if result:
            # Remove user_id prefix from keys if present
            keys = []
            for row in result:
                key = row[0]
                if user_id and key.startswith(f"{user_id}:"):
                    key = key[len(f"{user_id}:") :]
                keys.append(key)
            return keys
        return []

    async def clear(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> int:
        """Clear all keys matching an optional pattern."""
        await self._ensure_initialized()

        if user_id:
            if pattern:
                query = (
                    f"DELETE FROM {self.table_name} WHERE user_id = ? AND key GLOB ?"
                )
                glob_pattern = f"{user_id}:{pattern}"
                await asyncio.to_thread(
                    self.database.execute, query, user_id, glob_pattern
                )
            else:
                query = f"DELETE FROM {self.table_name} WHERE user_id = ?"
                await asyncio.to_thread(self.database.execute, query, user_id)
        else:
            if pattern:
                query = f"DELETE FROM {self.table_name} WHERE key GLOB ?"
                await asyncio.to_thread(self.database.execute, query, pattern)
            else:
                query = f"DELETE FROM {self.table_name}"
                await asyncio.to_thread(self.database.execute, query)

        # Get number of deleted rows
        changes_query = "SELECT changes()"
        changes = await asyncio.to_thread(self.database.execute, changes_query)
        return changes[0][0] if changes else 0

    async def size(self, user_id: Optional[str] = None) -> int:
        """Get the number of keys in memory."""
        await self._ensure_initialized()

        if user_id:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE user_id = ?"
            result = await asyncio.to_thread(self.database.execute, query, user_id)
        else:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            result = await asyncio.to_thread(self.database.execute, query)

        return result[0][0] if result else 0

    def health_check(self) -> bool:
        """Check if the memory system is healthy."""
        try:
            # Check database health
            if not self.database.health_check():
                return False

            # Check vector store health
            if not self.vector_store.health_check():
                return False

            return True
        except Exception:
            return False


class MemoryDecorator(ABC):
    """Abstract base class for memory decorators.

    All decorators should inherit from this class and implement
    the IMemory protocol while wrapping another IMemory instance.
    """

    def __init__(self, memory: IMemory):
        """Initialize decorator with wrapped memory instance.

        Args:
            memory: The memory instance to wrap
        """
        self._memory = memory

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with the given key."""
        return await self._memory.store(key, value, user_id)

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value by key."""
        return await self._memory.load(key, default, user_id)

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key from memory."""
        return await self._memory.delete(key, user_id)

    async def exists(self, key: str, user_id: Optional[str] = None) -> bool:
        """Check if a key exists in memory."""
        return await self._memory.exists(key, user_id)

    async def keys(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[str]:
        """Get all keys matching an optional pattern."""
        return await self._memory.keys(pattern, user_id)

    async def clear(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> int:
        """Clear all keys matching an optional pattern."""
        return await self._memory.clear(pattern, user_id)

    async def size(self, user_id: Optional[str] = None) -> int:
        """Get the number of keys in memory."""
        return await self._memory.size(user_id)

    def health_check(self) -> bool:
        """Check if the memory system is healthy."""
        return self._memory.health_check()
