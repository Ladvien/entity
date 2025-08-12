"""Async database resource that executes queries using async database backends."""

from __future__ import annotations

from typing import Any

from entity.infrastructure.async_duckdb_infra import AsyncDuckDBInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class AsyncDatabaseResource:
    """Layer 2 async database resource providing truly asynchronous database access.

    This resource eliminates the need for asyncio.to_thread() by using native
    async database operations. It maintains backward compatibility while providing
    better performance and proper async patterns.
    """

    def __init__(self, infrastructure: AsyncDuckDBInfrastructure | None) -> None:
        """Initialize with an async database infrastructure.

        Args:
            infrastructure: Async database infrastructure instance

        Raises:
            ResourceInitializationError: If infrastructure is None
        """
        if infrastructure is None:
            raise ResourceInitializationError("AsyncDuckDBInfrastructure is required")
        self.infrastructure = infrastructure

    async def health_check(self) -> bool:
        """Check if the underlying infrastructure is healthy.

        Returns:
            True if the database is operational, False otherwise
        """
        return await self.infrastructure.health_check()

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for backward compatibility.

        Note: This method should be avoided in async contexts.
        Use health_check() instead for better performance.
        """
        return self.infrastructure.health_check_sync()

    async def execute(self, query: str, *params: object) -> Any:
        """Execute a SQL query asynchronously and return the result.

        This is the main async method that replaces the sync execute() pattern
        wrapped in asyncio.to_thread().

        Args:
            query: SQL query string to execute
            *params: Query parameters to bind

        Returns:
            Query result cursor or data based on query type

        Examples:
            >>> # Create table
            >>> await db.execute(
            ...     "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
            ... )
            >>>
            >>> # Insert data
            >>> await db.execute(
            ...     "INSERT INTO users (name) VALUES (?)", "Alice"
            ... )
            >>>
            >>> # Query data
            >>> cursor = await db.execute("SELECT * FROM users WHERE name = ?", "Alice")
        """
        return await self.infrastructure.execute_async(query, params)

    async def execute_fetch_one(self, query: str, *params: object) -> Any:
        """Execute a query and return only the first row.

        Args:
            query: SQL query string to execute
            *params: Query parameters to bind

        Returns:
            First row of the result set, or None if no results

        Examples:
            >>> user = await db.execute_fetch_one(
            ...     "SELECT * FROM users WHERE id = ?", user_id
            ... )
            >>> if user:
            ...     print(f"Found user: {user[1]}")
        """
        return await self.infrastructure.execute_async(query, params, fetch_one=True)

    async def execute_fetch_all(self, query: str, *params: object) -> list[Any]:
        """Execute a query and return all rows.

        Args:
            query: SQL query string to execute
            *params: Query parameters to bind

        Returns:
            List of all rows in the result set

        Examples:
            >>> users = await db.execute_fetch_all("SELECT * FROM users")
            >>> for user in users:
            ...     print(f"User: {user[1]}")
        """
        return await self.infrastructure.execute_fetch_all(
            query, params, fetch_all=True
        )

    async def execute_script(self, script: str) -> None:
        """Execute a multi-statement SQL script asynchronously.

        Args:
            script: SQL script with multiple statements separated by semicolons

        Examples:
            >>> await db.execute_script('''
            ...     CREATE TABLE IF NOT EXISTS users (
            ...         id INTEGER PRIMARY KEY,
            ...         name TEXT NOT NULL,
            ...         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ...     );
            ...     CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);
            ... ''')
        """
        await self.infrastructure.execute_script(script)

    async def execute_many(self, query: str, parameters_list: list[tuple]) -> None:
        """Execute a query multiple times with different parameter sets.

        This is more efficient than multiple individual execute() calls.

        Args:
            query: SQL query string with parameter placeholders
            parameters_list: List of parameter tuples

        Examples:
            >>> users_data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
            >>> await db.execute_many(
            ...     "INSERT INTO users (name, age) VALUES (?, ?)",
            ...     users_data
            ... )
        """
        await self.infrastructure.execute_many(query, parameters_list)

    async def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool statistics for monitoring and debugging.

        Returns:
            Dictionary containing connection pool metrics

        Examples:
            >>> stats = await db.get_connection_stats()
            >>> print(f"Active connections: {stats['active_connections']}")
            >>> print(f"Pool size: {stats['pool_size']}")
        """
        return await self.infrastructure.get_connection_stats()

    def execute_sync(self, query: str, *params: object) -> Any:
        """Synchronous wrapper for execute() for backward compatibility.

        WARNING: This method should be avoided in async contexts as it will
        block the event loop. Use execute() instead.

        Args:
            query: SQL query string to execute
            *params: Query parameters to bind

        Returns:
            Query result cursor
        """
        import asyncio

        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "execute_sync() called from async context. Use execute() instead."
            )
        except RuntimeError:
            return asyncio.run(self.execute(query, *params))

    def connect(self):
        """Synchronous context manager for backward compatibility.

        WARNING: This method provides sync-style access but still requires
        the infrastructure to be started with async startup().
        Use async context manager patterns instead where possible.

        Returns:
            Synchronous database connection wrapper
        """
        return _SyncConnectionWrapper(self.infrastructure)


class _SyncConnectionWrapper:
    """Wrapper to provide synchronous connection interface for backward compatibility."""

    def __init__(self, infrastructure: AsyncDuckDBInfrastructure):
        self.infrastructure = infrastructure
        self._conn = None

    def __enter__(self):
        """Enter synchronous context manager."""
        import asyncio

        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "Synchronous database connection used in async context. "
                "Use 'async with infrastructure.connect()' instead."
            )
        except RuntimeError:

            async def _get_connection():
                async with self.infrastructure.connect() as conn:
                    return conn

            self._conn = asyncio.run(_get_connection())
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit synchronous context manager."""
        if self._conn:
            import asyncio

            asyncio.run(self._conn.close())

    def execute(self, query: str, params=None):
        """Execute query synchronously."""
        if not self._conn:
            raise RuntimeError("Connection not established")

        import asyncio

        params = params or ()
        return asyncio.run(self._conn.execute(query, params))
