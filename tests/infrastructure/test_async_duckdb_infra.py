"""Tests for async DuckDB infrastructure."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from entity.infrastructure.async_duckdb_infra import AsyncDuckDBInfrastructure


class TestAsyncDuckDBInfrastructure:
    """Test suite for AsyncDuckDBInfrastructure."""

    @pytest.fixture
    async def temp_db_path(self):
        """Create temporary database file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield str(Path(temp_dir) / "test.db")

    @pytest.fixture
    async def memory_infra(self):
        """Create in-memory async infrastructure."""
        infra = AsyncDuckDBInfrastructure(":memory:")
        await infra.startup()
        yield infra
        await infra.shutdown()

    @pytest.fixture
    async def file_infra(self, temp_db_path):
        """Create file-based async infrastructure."""
        infra = AsyncDuckDBInfrastructure(temp_db_path, pool_size=3)
        await infra.startup()
        yield infra
        await infra.shutdown()

    @pytest.mark.asyncio
    async def test_infrastructure_startup_shutdown(self, temp_db_path):
        """Test infrastructure startup and shutdown."""
        infra = AsyncDuckDBInfrastructure(temp_db_path)

        # Should not be started initially
        assert not infra._is_started

        await infra.startup()
        assert infra._is_started

        await infra.shutdown()
        assert not infra._is_started

    @pytest.mark.asyncio
    async def test_memory_database_operations(self, memory_infra):
        """Test basic operations with in-memory database."""
        # Test table creation
        await memory_infra.execute_async(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        )

        # Test insert
        await memory_infra.execute_async(
            "INSERT INTO test (id, name) VALUES (?, ?)", (1, "Alice")
        )

        # Test select with fetch_one
        row = await memory_infra.execute_async(
            "SELECT * FROM test WHERE id = ?", (1,), fetch_one=True
        )
        assert row == (1, "Alice")

        # Test select with fetch_all
        rows = await memory_infra.execute_async("SELECT * FROM test", fetch_all=True)
        assert len(rows) == 1
        assert rows[0] == (1, "Alice")

    @pytest.mark.asyncio
    async def test_file_database_operations(self, file_infra, temp_db_path):
        """Test operations with file-based database."""
        # Verify file path is set correctly
        assert file_infra.file_path == temp_db_path

        # Test table creation and data persistence
        await file_infra.execute_async(
            "CREATE TABLE persistent_test (id INTEGER, data TEXT)"
        )

        await file_infra.execute_async(
            "INSERT INTO persistent_test VALUES (1, 'test_data')"
        )

        # Verify data exists
        row = await file_infra.execute_async(
            "SELECT * FROM persistent_test WHERE id = 1", fetch_one=True
        )
        assert row == (1, "test_data")

    @pytest.mark.asyncio
    async def test_connection_pooling(self, file_infra):
        """Test connection pool functionality."""
        # Get initial stats
        stats = await file_infra.get_connection_stats()
        assert stats["pool_size"] == 3
        assert stats["is_started"] is True

        # Test concurrent connections
        async def concurrent_query(query_id):
            result = await file_infra.execute_async(
                "SELECT ? as query_id", (query_id,), fetch_one=True
            )
            return result[0]

        # Run concurrent queries to test pooling
        tasks = [concurrent_query(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all queries completed correctly
        assert results == list(range(5))

    @pytest.mark.asyncio
    async def test_query_timeout(self, memory_infra):
        """Test query timeout functionality."""
        # Set a very short timeout for testing
        original_timeout = memory_infra.query_timeout
        memory_infra.query_timeout = 0.001  # 1ms

        try:
            # Create a slow query by using a long loop in SQLite
            with pytest.raises(asyncio.TimeoutError):
                await memory_infra.execute_async(
                    "WITH RECURSIVE slow_query(x) AS (SELECT 0 UNION ALL SELECT x+1 FROM slow_query WHERE x < 100000) SELECT COUNT(*) FROM slow_query"
                )
        finally:
            # Restore original timeout
            memory_infra.query_timeout = original_timeout

    @pytest.mark.asyncio
    async def test_execute_script(self, memory_infra):
        """Test script execution."""
        script = """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT);
        INSERT INTO users (name) VALUES ('Alice'), ('Bob');
        INSERT INTO posts (user_id, title) VALUES (1, 'First Post'), (2, 'Second Post');
        """

        await memory_infra.execute_script(script)

        # Verify script execution
        users = await memory_infra.execute_async("SELECT * FROM users", fetch_all=True)
        posts = await memory_infra.execute_async("SELECT * FROM posts", fetch_all=True)

        assert len(users) == 2
        assert len(posts) == 2

    @pytest.mark.asyncio
    async def test_execute_many(self, memory_infra):
        """Test batch execution."""
        # Create table
        await memory_infra.execute_async(
            "CREATE TABLE batch_test (id INTEGER, name TEXT)"
        )

        # Prepare batch data
        batch_data = [(i, f"name_{i}") for i in range(10)]

        # Execute batch
        await memory_infra.execute_many(
            "INSERT INTO batch_test (id, name) VALUES (?, ?)", batch_data
        )

        # Verify batch insertion
        rows = await memory_infra.execute_async(
            "SELECT COUNT(*) FROM batch_test", fetch_one=True
        )
        assert rows[0] == 10

    @pytest.mark.asyncio
    async def test_health_check(self, memory_infra):
        """Test health check functionality."""
        # Should be healthy after startup
        assert await memory_infra.health_check() is True

        # Test sync health check
        assert memory_infra.health_check_sync() is True

    @pytest.mark.asyncio
    async def test_connection_stats(self, file_infra):
        """Test connection statistics."""
        stats = await file_infra.get_connection_stats()

        required_keys = [
            "pool_size",
            "active_connections",
            "file_path",
            "query_timeout",
            "is_started",
        ]

        for key in required_keys:
            assert key in stats

        assert stats["pool_size"] == 3
        assert stats["is_started"] is True
        assert stats["query_timeout"] == 30.0

    @pytest.mark.asyncio
    async def test_error_handling(self, memory_infra):
        """Test error handling in database operations."""
        # Test invalid SQL
        with pytest.raises(Exception):
            await memory_infra.execute_async("INVALID SQL STATEMENT")

        # Test invalid parameters
        with pytest.raises(Exception):
            await memory_infra.execute_async(
                "SELECT ? FROM nonexistent_table", ("param",)
            )

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, file_infra):
        """Test high concurrency operations."""
        # Create test table
        await file_infra.execute_async(
            "CREATE TABLE concurrent_test (id INTEGER, thread_id INTEGER)"
        )

        async def worker_task(worker_id, num_ops):
            for i in range(num_ops):
                await file_infra.execute_async(
                    "INSERT INTO concurrent_test (id, thread_id) VALUES (?, ?)",
                    (i, worker_id),
                )

        # Run concurrent workers
        num_workers = 5
        ops_per_worker = 10

        tasks = [
            worker_task(worker_id, ops_per_worker) for worker_id in range(num_workers)
        ]
        await asyncio.gather(*tasks)

        # Verify all operations completed
        total_rows = await file_infra.execute_async(
            "SELECT COUNT(*) FROM concurrent_test", fetch_one=True
        )

        assert total_rows[0] == num_workers * ops_per_worker

    @pytest.mark.asyncio
    async def test_database_file_creation(self):
        """Test that database file is created in correct location."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "subdir" / "test.db"

            # Directory doesn't exist yet
            assert not db_path.parent.exists()

            infra = AsyncDuckDBInfrastructure(str(db_path))
            await infra.startup()

            try:
                # Create a table to force file creation
                await infra.execute_async("CREATE TABLE test (id INTEGER)")

                # Directory should now exist
                assert db_path.parent.exists()

            finally:
                await infra.shutdown()

    @pytest.mark.asyncio
    async def test_startup_without_startup_call(self):
        """Test that operations fail if startup() is not called."""
        infra = AsyncDuckDBInfrastructure(":memory:")

        # Should fail without startup
        with pytest.raises(RuntimeError, match="Infrastructure not started"):
            async with infra.connect():
                pass

    @pytest.mark.asyncio
    async def test_connection_context_manager(self, memory_infra):
        """Test connection context manager functionality."""
        async with memory_infra.connect() as conn:
            # Connection should be usable
            cursor = await conn.execute("SELECT 1 as test")
            row = await cursor.fetchone()
            assert row[0] == 1

        # Connection should be returned to pool after context exit
