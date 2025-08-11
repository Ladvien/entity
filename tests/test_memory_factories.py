"""Tests for memory factory functions and backward compatibility."""

import warnings
from unittest.mock import patch

import pytest

from entity.resources.memory_factories import (
    AsyncMemory,
    ManagedMemory,
    Memory,
    RobustMemory,
    create_async_memory,
    create_full_featured_memory,
    create_managed_memory,
    create_memory,
    create_robust_memory,
)


class MockDatabaseResource:
    """Mock database resource for testing."""

    def __init__(self):
        self.queries = []
        self.data = {}  # Store data for SELECT queries

    def execute(self, query, *params):
        self.queries.append((query, params))

        # Handle INSERT/REPLACE
        if "INSERT OR REPLACE" in query and "entity_memory" in query:
            # Extract key and value from params (first two params)
            if len(params) >= 2:
                key, value = params[0], params[1]
                self.data[key] = value
            return None

        # Handle SELECT for retrieving values
        if "SELECT value FROM entity_memory WHERE key = ?" in query:
            if params and params[0] in self.data:
                return [(self.data[params[0]],)]
            return []

        # Handle SELECT changes()
        if "SELECT changes()" in query:
            return [(1,)]

        # Handle other SELECT queries
        if "SELECT" in query:
            return []

        return None

    def health_check(self):
        return True

    def health_check_sync(self):
        return True


class MockVectorStoreResource:
    """Mock vector store resource for testing."""

    def __init__(self):
        self.vectors = {}

    def add_vector(self, table, vector):
        if table not in self.vectors:
            self.vectors[table] = []
        self.vectors[table].append(vector)

    def query(self, query):
        return []

    def health_check(self):
        return True

    def health_check_sync(self):
        return True


@pytest.mark.asyncio
class TestMemoryFactories:
    """Tests for memory factory functions."""

    async def test_create_memory(self):
        """Test basic memory creation."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        memory = create_memory(db, vector_store)

        # Should return a memory instance that implements IMemory
        assert hasattr(memory, "store")
        assert hasattr(memory, "load")
        assert hasattr(memory, "delete")
        assert hasattr(memory, "exists")
        assert hasattr(memory, "keys")
        assert hasattr(memory, "clear")
        assert hasattr(memory, "size")
        assert hasattr(memory, "health_check")

        # Test basic operations
        await memory.store("test_key", "test_value")
        # Check that database was called
        assert any("INSERT" in q[0] for q in db.queries)

    async def test_create_async_memory(self):
        """Test async memory creation."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        memory = create_async_memory(db, vector_store, max_workers=5)

        # Should be able to use async operations
        await memory.store("test_key", "test_value")
        await memory.load("test_key", default="default")

        # Verify it's using AsyncDecorator features
        from entity.resources.memory_decorators import AsyncDecorator

        assert isinstance(memory, AsyncDecorator)

    async def test_create_managed_memory(self):
        """Test managed memory creation with TTL and LRU."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        memory = create_managed_memory(
            db, vector_store, default_ttl=3600, max_entries=100, evict_count=10
        )

        # Should have TTL and LRU features
        from entity.resources.memory_decorators import LRUDecorator, TTLDecorator

        # Check decorator chain
        assert isinstance(memory, LRUDecorator)
        # The wrapped memory should be TTLDecorator
        assert isinstance(memory._memory, TTLDecorator)

        # Test TTL functionality
        await memory.store("test_key", "test_value")
        ttl = await memory._memory.get_ttl("test_key")
        assert ttl is not None
        assert ttl > 0

    async def test_create_robust_memory(self):
        """Test robust memory creation with locking and monitoring."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None

            memory = create_robust_memory(
                db,
                vector_store,
                lock_dir="/tmp/test_locks",
                timeout=5.0,
                enable_monitoring=True,
            )

            # Should have locking and monitoring features
            from entity.resources.memory_decorators import (
                LockingDecorator,
                MonitoringDecorator,
            )

            # Check decorator chain
            assert isinstance(memory, MonitoringDecorator)
            assert isinstance(memory._memory, LockingDecorator)

            # Test monitoring functionality
            await memory.store("test_key", "test_value")
            metrics = memory.get_metrics()
            assert metrics["operations"]["store"]["count"] == 1

    async def test_create_full_featured_memory(self):
        """Test full-featured memory with all decorators."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None

            memory = create_full_featured_memory(
                db,
                vector_store,
                default_ttl=3600,
                max_entries=1000,
                evict_count=100,
                cleanup_interval=60,
                lock_dir="/tmp/test_locks",
                lock_timeout=10.0,
                enable_monitoring=True,
                async_workers=10,
            )

            # Should have all features
            from entity.resources.memory_decorators import MonitoringDecorator

            # Top level should be monitoring
            assert isinstance(memory, MonitoringDecorator)

            # Test full functionality
            await memory.store("test_key", "test_value")
            result = await memory.load("test_key")
            assert result == "test_value"

            # Check metrics are being collected
            metrics = memory.get_metrics()
            assert metrics["operations"]["store"]["count"] >= 1
            assert metrics["operations"]["load"]["count"] >= 1


class TestBackwardCompatibility:
    """Tests for backward compatibility with deprecated classes."""

    def test_memory_class_deprecation_warning(self):
        """Test that Memory class shows deprecation warning."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Memory(db, vector_store)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "create_memory()" in str(w[0].message)

    def test_async_memory_class_deprecation_warning(self):
        """Test that AsyncMemory class shows deprecation warning."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            AsyncMemory(db, vector_store)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "create_async_memory()" in str(w[0].message)

    def test_managed_memory_class_deprecation_warning(self):
        """Test that ManagedMemory class shows deprecation warning."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ManagedMemory(db, vector_store)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "create_managed_memory()" in str(w[0].message)

    def test_robust_memory_class_deprecation_warning(self):
        """Test that RobustMemory class shows deprecation warning."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                RobustMemory(db, vector_store)

                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
                assert "create_robust_memory()" in str(w[0].message)

    async def test_deprecated_classes_still_work(self):
        """Test that deprecated classes still function correctly."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Test Memory class
            memory = Memory(db, vector_store)
            await memory.store("key1", "value1")

            # Test AsyncMemory class
            async_memory = AsyncMemory(db, vector_store)
            await async_memory.store("key2", "value2")

            # Test ManagedMemory class
            managed_memory = ManagedMemory(db, vector_store, default_ttl=None)
            await managed_memory.store("key3", "value3")

            # All should work without errors
            assert True  # If we get here, everything worked


@pytest.mark.asyncio
class TestFactoryParameters:
    """Tests for factory function parameters."""

    async def test_custom_table_name(self):
        """Test using custom table name."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        memory = create_memory(db, vector_store, table_name="custom_table")

        await memory.store("test_key", "test_value")

        # Check that custom table name was used
        assert any("custom_table" in q[0] for q in db.queries)

    async def test_ttl_disabled(self):
        """Test managed memory with TTL disabled."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        memory = create_managed_memory(
            db,
            vector_store,
            default_ttl=None,
            max_entries=100,  # Disable TTL
        )

        from entity.resources.memory_decorators import LRUDecorator, TTLDecorator

        # Should only have LRU, not TTL
        assert isinstance(memory, LRUDecorator)
        assert not isinstance(memory._memory, TTLDecorator)

    async def test_monitoring_disabled(self):
        """Test robust memory with monitoring disabled."""
        db = MockDatabaseResource()
        vector_store = MockVectorStoreResource()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None

            memory = create_robust_memory(
                db,
                vector_store,
                enable_monitoring=False,  # Disable monitoring
            )

            from entity.resources.memory_decorators import (
                LockingDecorator,
                MonitoringDecorator,
            )

            # Should only have locking, not monitoring
            assert isinstance(memory, LockingDecorator)
            assert not isinstance(memory, MonitoringDecorator)
