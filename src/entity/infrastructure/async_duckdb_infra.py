"""Asynchronous DuckDB infrastructure implementation."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

import aiosqlite

from .base import BaseInfrastructure


class AsyncDuckDBInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for managing async DuckDB-compatible database operations.

    This implementation uses aiosqlite for truly asynchronous database operations,
    eliminating the need for asyncio.to_thread() wrappers around synchronous calls.
    It provides connection pooling, query timeouts, and performance optimizations.
    """

    def __init__(
        self,
        file_path: str,
        pool_size: int = 5,
        query_timeout: float = 30.0,
        version: str | None = None,
    ) -> None:
        """Initialize the async database infrastructure.

        Args:
            file_path: Path to the database file, or ":memory:" for in-memory DB
            pool_size: Maximum number of connections in the pool (ignored for in-memory)
            query_timeout: Maximum time in seconds to wait for query execution
            version: Optional version string for infrastructure tracking
        """
        super().__init__(version)
        self.file_path = file_path
        self.pool_size = pool_size if file_path != ":memory:" else 1
        self.query_timeout = query_timeout
        self._pool: list[aiosqlite.Connection] = []
        self._pool_semaphore: Optional[asyncio.Semaphore] = None
        self._pool_lock = asyncio.Lock()
        self._is_started = False

    async def startup(self) -> None:
        """Initialize the connection pool and prepare the database."""
        await super().startup()

        # Initialize pool semaphore
        self._pool_semaphore = asyncio.Semaphore(self.pool_size)

        # Pre-populate the connection pool for better performance
        async with self._pool_lock:
            for _ in range(min(2, self.pool_size)):  # Start with 2 connections
                conn = await self._create_connection()
                self._pool.append(conn)

        self._is_started = True
        self.logger.info(
            "Async database infrastructure ready: %s (pool_size=%d, timeout=%.1fs)",
            self.file_path,
            self.pool_size,
            self.query_timeout,
        )

    async def shutdown(self) -> None:
        """Clean up all connections and close the pool."""
        await super().shutdown()
        self._is_started = False

        # Close all pooled connections
        async with self._pool_lock:
            while self._pool:
                conn = self._pool.pop()
                try:
                    await conn.close()
                except Exception as e:
                    self.logger.warning("Error closing connection: %s", e)

        self.logger.info("Async database infrastructure shut down")

    async def _create_connection(self) -> aiosqlite.Connection:
        """Create a new database connection with proper configuration."""
        if self.file_path == ":memory:":
            # For in-memory databases, we need to use a shared cache
            conn = await aiosqlite.connect(
                ":memory:",
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode
            )
        else:
            # Ensure directory exists
            Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)

            conn = await aiosqlite.connect(
                self.file_path,
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode
            )

        # Configure connection for better performance
        await conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        await conn.execute("PRAGMA synchronous=NORMAL")  # Balanced performance/safety
        await conn.execute("PRAGMA temp_store=memory")  # Use memory for temp tables
        await conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory map

        return conn

    async def _acquire_connection(self) -> aiosqlite.Connection:
        """Acquire a connection from the pool or create a new one."""
        if not self._is_started:
            raise RuntimeError("Infrastructure not started. Call startup() first.")

        # Use semaphore to limit concurrent connections
        await self._pool_semaphore.acquire()

        try:
            # Try to get a connection from the pool
            async with self._pool_lock:
                if self._pool:
                    return self._pool.pop()

            # Pool is empty, create a new connection
            return await self._create_connection()

        except Exception:
            # Release semaphore if connection acquisition fails
            self._pool_semaphore.release()
            raise

    async def _release_connection(self, conn: aiosqlite.Connection) -> None:
        """Return a connection to the pool or close it if pool is full."""
        try:
            async with self._pool_lock:
                if len(self._pool) < self.pool_size:
                    self._pool.append(conn)
                else:
                    # Pool is full, close the connection
                    await conn.close()
        finally:
            # Always release the semaphore
            self._pool_semaphore.release()

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Async context manager that yields a database connection.

        This replaces the synchronous context manager from the base class.
        The connection is automatically returned to the pool when done.

        Examples:
            >>> async with infrastructure.connect() as conn:
            ...     cursor = await conn.execute("SELECT * FROM table")
            ...     rows = await cursor.fetchall()
        """
        conn = await self._acquire_connection()
        try:
            yield conn
        finally:
            await self._release_connection(conn)

    async def execute_async(
        self,
        query: str,
        parameters: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = False,
    ) -> Any:
        """Execute a query asynchronously with automatic connection management.

        Args:
            query: SQL query string to execute
            parameters: Query parameters as a tuple
            fetch_one: If True, return only the first row
            fetch_all: If True, return all rows as a list

        Returns:
            Query result based on fetch options, or the cursor if no fetch specified

        Examples:
            >>> # Insert data
            >>> await infra.execute_async(
            ...     "INSERT INTO users (name, age) VALUES (?, ?)",
            ...     ("Alice", 30)
            ... )
            >>>
            >>> # Fetch one row
            >>> user = await infra.execute_async(
            ...     "SELECT * FROM users WHERE id = ?",
            ...     (1,),
            ...     fetch_one=True
            ... )
            >>>
            >>> # Fetch all rows
            >>> users = await infra.execute_async(
            ...     "SELECT * FROM users",
            ...     fetch_all=True
            ... )
        """
        async with self.connect() as conn:
            try:
                # Execute with timeout
                cursor = await asyncio.wait_for(
                    conn.execute(query, parameters), timeout=self.query_timeout
                )

                if fetch_one:
                    return await cursor.fetchone()
                elif fetch_all:
                    return await cursor.fetchall()
                else:
                    return cursor

            except asyncio.TimeoutError:
                self.logger.error(
                    "Query timeout after %.1fs: %s", self.query_timeout, query[:100]
                )
                raise
            except Exception as e:
                self.logger.error(
                    "Query execution error: %s - Query: %s", e, query[:100]
                )
                raise

    async def health_check(self) -> bool:
        """Check if the database is accessible and operational.

        Returns:
            True if the database is healthy, False otherwise
        """
        try:
            # Test basic connectivity and functionality
            result = await self.execute_async(
                "SELECT 1 as health_check", fetch_one=True
            )

            if result and result[0] == 1:
                self.logger.debug("Health check succeeded for %s", self.file_path)
                return True
            else:
                self.logger.warning(
                    "Health check returned unexpected result: %s", result
                )
                return False

        except Exception as exc:
            self.logger.warning("Health check failed for %s: %s", self.file_path, exc)
            return False

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for backward compatibility.

        This method should be avoided in async contexts - use health_check() instead.
        """
        try:
            # Run the async health check in the current event loop
            loop = asyncio.get_running_loop()
            task = loop.create_task(self.health_check())
            # Give it a short timeout to prevent blocking
            return asyncio.run_coroutine_threadsafe(task, loop).result(timeout=5.0)
        except Exception:
            # Fall back to basic sync check if async fails
            try:
                import sqlite3

                if self.file_path == ":memory:":
                    return True  # Memory DB is always "healthy"

                # Test file access
                conn = sqlite3.connect(self.file_path, timeout=1.0)
                conn.execute("SELECT 1")
                conn.close()
                return True
            except Exception:
                return False

    async def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool statistics for monitoring.

        Returns:
            Dictionary with pool statistics
        """
        async with self._pool_lock:
            return {
                "pool_size": self.pool_size,
                "active_connections": len(self._pool),
                "available_permits": (
                    self._pool_semaphore.locked() if self._pool_semaphore else 0
                ),
                "file_path": self.file_path,
                "query_timeout": self.query_timeout,
                "is_started": self._is_started,
            }

    async def execute_script(self, script: str) -> None:
        """Execute a multi-statement SQL script asynchronously.

        Args:
            script: SQL script with multiple statements

        Examples:
            >>> await infra.execute_script('''
            ...     CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
            ...     CREATE INDEX idx_users_name ON users(name);
            ...     INSERT INTO users (name) VALUES ('Alice'), ('Bob');
            ... ''')
        """
        async with self.connect() as conn:
            try:
                await asyncio.wait_for(
                    conn.executescript(script),
                    timeout=self.query_timeout * 2,  # Scripts may take longer
                )
            except asyncio.TimeoutError:
                self.logger.error("Script timeout after %.1fs", self.query_timeout * 2)
                raise
            except Exception as e:
                self.logger.error("Script execution error: %s", e)
                raise

    async def execute_many(self, query: str, parameters_list: list[tuple]) -> None:
        """Execute a query multiple times with different parameters.

        Args:
            query: SQL query string with parameter placeholders
            parameters_list: List of parameter tuples

        Examples:
            >>> await infra.execute_many(
            ...     "INSERT INTO users (name, age) VALUES (?, ?)",
            ...     [("Alice", 30), ("Bob", 25), ("Charlie", 35)]
            ... )
        """
        async with self.connect() as conn:
            try:
                await asyncio.wait_for(
                    conn.executemany(query, parameters_list),
                    timeout=self.query_timeout
                    * len(parameters_list)
                    / 100,  # Scale with batch size
                )
            except asyncio.TimeoutError:
                self.logger.error(
                    "Batch execution timeout for %d statements", len(parameters_list)
                )
                raise
            except Exception as e:
                self.logger.error("Batch execution error: %s", e)
                raise
