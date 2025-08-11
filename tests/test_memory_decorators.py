"""Tests for memory decorator implementations."""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from entity.resources.memory_decorators import (
    AsyncDecorator,
    LockingDecorator,
    LRUDecorator,
    MonitoringDecorator,
    TTLDecorator,
)


class MockMemory:
    """Mock memory implementation for testing decorators."""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.call_counts = {
            "store": 0,
            "load": 0,
            "delete": 0,
            "exists": 0,
            "keys": 0,
            "clear": 0,
            "size": 0,
        }

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        self.call_counts["store"] += 1
        scoped_key = f"{user_id}:{key}" if user_id else key
        self.data[scoped_key] = value

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        self.call_counts["load"] += 1
        scoped_key = f"{user_id}:{key}" if user_id else key
        return self.data.get(scoped_key, default)

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        self.call_counts["delete"] += 1
        scoped_key = f"{user_id}:{key}" if user_id else key
        if scoped_key in self.data:
            del self.data[scoped_key]
            return True
        return False

    async def exists(self, key: str, user_id: Optional[str] = None) -> bool:
        self.call_counts["exists"] += 1
        scoped_key = f"{user_id}:{key}" if user_id else key
        return scoped_key in self.data

    async def keys(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[str]:
        self.call_counts["keys"] += 1
        keys = list(self.data.keys())
        if user_id:
            prefix = f"{user_id}:"
            keys = [k[len(prefix) :] for k in keys if k.startswith(prefix)]
        if pattern:
            # Simple glob pattern matching
            import fnmatch

            keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
        return keys

    async def clear(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> int:
        self.call_counts["clear"] += 1
        keys_to_delete = await self.keys(pattern, user_id)
        for key in keys_to_delete:
            await self.delete(key, user_id)
        return len(keys_to_delete)

    async def size(self, user_id: Optional[str] = None) -> int:
        self.call_counts["size"] += 1
        if user_id:
            prefix = f"{user_id}:"
            return sum(1 for k in self.data.keys() if k.startswith(prefix))
        return len(self.data)

    def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
class TestTTLDecorator:
    """Tests for TTL decorator functionality."""

    async def test_store_with_default_ttl(self):
        """Test storing values with default TTL."""
        mock_memory = MockMemory()
        ttl_memory = TTLDecorator(mock_memory, default_ttl=1)

        await ttl_memory.store("key1", "value1")
        assert await ttl_memory.load("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)
        await ttl_memory._cleanup_expired()

        assert await ttl_memory.load("key1") is None

    async def test_store_with_specific_ttl(self):
        """Test storing values with specific TTL."""
        mock_memory = MockMemory()
        ttl_memory = TTLDecorator(mock_memory)

        await ttl_memory.store_with_ttl("key1", "value1", ttl=1)
        assert await ttl_memory.load("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)
        await ttl_memory._cleanup_expired()

        assert await ttl_memory.load("key1") is None

    async def test_get_ttl(self):
        """Test getting remaining TTL for a key."""
        mock_memory = MockMemory()
        ttl_memory = TTLDecorator(mock_memory)

        await ttl_memory.store_with_ttl("key1", "value1", ttl=10)

        remaining_ttl = await ttl_memory.get_ttl("key1")
        assert remaining_ttl is not None
        assert 8 <= remaining_ttl <= 10  # Allow for small timing variations

        # Key without TTL
        await mock_memory.store("key2", "value2")
        assert await ttl_memory.get_ttl("key2") is None

    async def test_delete_with_ttl(self):
        """Test deleting a key removes TTL tracking."""
        mock_memory = MockMemory()
        ttl_memory = TTLDecorator(mock_memory)

        await ttl_memory.store_with_ttl("key1", "value1", ttl=10)
        assert await ttl_memory.get_ttl("key1") is not None

        await ttl_memory.delete("key1")
        assert await ttl_memory.get_ttl("key1") is None

    async def test_cleanup_task_shutdown(self):
        """Test cleanup task shutdown."""
        mock_memory = MockMemory()
        ttl_memory = TTLDecorator(mock_memory, cleanup_interval=1)

        # Let cleanup task start
        await asyncio.sleep(0.1)

        # Shutdown should cancel the task
        await ttl_memory.shutdown()
        assert ttl_memory._cleanup_task.done()


@pytest.mark.asyncio
class TestLRUDecorator:
    """Tests for LRU decorator functionality."""

    async def test_lru_eviction(self):
        """Test LRU eviction when max entries reached."""
        mock_memory = MockMemory()
        lru_memory = LRUDecorator(mock_memory, max_entries=3, evict_count=1)

        # Store 3 entries
        await lru_memory.store("key1", "value1")
        await lru_memory.store("key2", "value2")
        await lru_memory.store("key3", "value3")

        # Access key1 to make it recently used
        await lru_memory.load("key1")

        # Store 4th entry should evict key2 (least recently used)
        await lru_memory.store("key4", "value4")

        assert await lru_memory.load("key1") == "value1"
        assert await lru_memory.load("key2") is None  # Evicted
        assert await lru_memory.load("key3") == "value3"
        assert await lru_memory.load("key4") == "value4"

    async def test_lru_access_tracking(self):
        """Test that accessing keys updates their LRU order."""
        mock_memory = MockMemory()
        lru_memory = LRUDecorator(mock_memory, max_entries=2, evict_count=1)

        await lru_memory.store("key1", "value1")
        await lru_memory.store("key2", "value2")

        # Access key1 multiple times
        await lru_memory.load("key1")
        await lru_memory.load("key1")

        # Store 3rd entry should evict key2 (less recently used)
        await lru_memory.store("key3", "value3")

        assert await lru_memory.load("key1") == "value1"  # Still present
        assert await lru_memory.load("key2") is None  # Evicted
        assert await lru_memory.load("key3") == "value3"

    async def test_lru_metrics(self):
        """Test LRU metrics collection."""
        mock_memory = MockMemory()
        lru_memory = LRUDecorator(mock_memory, max_entries=10)

        await lru_memory.store("key1", "value1")
        await lru_memory.load("key1")  # Hit
        await lru_memory.load("key2")  # Miss

        metrics = lru_memory.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["evictions"] == 0

    async def test_delete_removes_from_lru(self):
        """Test that deleting a key removes it from LRU tracking."""
        mock_memory = MockMemory()
        lru_memory = LRUDecorator(mock_memory, max_entries=3)

        await lru_memory.store("key1", "value1")
        await lru_memory.store("key2", "value2")

        # Delete key1
        await lru_memory.delete("key1")

        # Verify it's not in access order
        assert len(lru_memory._access_order) == 1
        assert "key2" in list(lru_memory._access_order.keys())[0]


@pytest.mark.asyncio
class TestLockingDecorator:
    """Tests for locking decorator functionality."""

    async def test_concurrent_access_protection(self):
        """Test that locking prevents concurrent access issues."""
        mock_memory = MockMemory()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None
            locking_memory = LockingDecorator(mock_memory, lock_dir="/tmp/test_locks")

            # Simulate concurrent stores
            async def concurrent_store(key: str, value: str):
                await locking_memory.store(key, value)

            # Run concurrent operations
            tasks = [concurrent_store("shared_key", f"value_{i}") for i in range(5)]

            await asyncio.gather(*tasks)

            # Should have one final value (last write wins)
            final_value = await locking_memory.load("shared_key")
            assert final_value is not None
            assert final_value.startswith("value_")

    async def test_lock_timeout(self):
        """Test lock acquisition timeout."""
        mock_memory = MockMemory()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None
            locking_memory = LockingDecorator(mock_memory, timeout=0.1)

            # Acquire lock manually
            await locking_memory._acquire_lock("test_key")

            # Try to acquire again (should timeout)
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(
                    locking_memory._acquire_lock("test_key"), timeout=0.2
                )

            # Release lock
            await locking_memory._release_lock("test_key")

    async def test_locking_metrics(self):
        """Test locking metrics collection."""
        mock_memory = MockMemory()

        with patch("entity.resources.memory_decorators.Path") as mock_path:
            mock_path.return_value.mkdir.return_value = None
            locking_memory = LockingDecorator(mock_memory)

            await locking_memory.store("key1", "value1")
            await locking_memory.load("key1")

            metrics = locking_memory.get_metrics()
            assert metrics["acquisitions"] == 2  # One for store, one for load
            assert metrics["timeouts"] == 0


@pytest.mark.asyncio
class TestAsyncDecorator:
    """Tests for async decorator functionality."""

    async def test_async_wrapper_for_sync_memory(self):
        """Test async decorator wraps synchronous operations."""
        # Create a sync memory mock
        sync_memory = Mock()
        sync_memory.store = Mock(return_value=None)
        sync_memory.load = Mock(return_value="value1")
        sync_memory.delete = Mock(return_value=True)
        sync_memory.exists = Mock(return_value=True)
        sync_memory.keys = Mock(return_value=["key1", "key2"])
        sync_memory.clear = Mock(return_value=2)
        sync_memory.size = Mock(return_value=5)

        async_memory = AsyncDecorator(sync_memory)

        # Test async operations
        await async_memory.store("key1", "value1")
        sync_memory.store.assert_called_once_with("key1", "value1", None)

        result = await async_memory.load("key1")
        assert result == "value1"
        sync_memory.load.assert_called_once_with("key1", None, None)

        deleted = await async_memory.delete("key1")
        assert deleted is True
        sync_memory.delete.assert_called_once_with("key1", None)

    async def test_async_wrapper_preserves_async_methods(self):
        """Test async decorator preserves already async methods."""
        mock_memory = MockMemory()
        async_memory = AsyncDecorator(mock_memory)

        # Should use the already async methods directly
        await async_memory.store("key1", "value1")
        assert mock_memory.call_counts["store"] == 1

        result = await async_memory.load("key1")
        assert result == "value1"
        assert mock_memory.call_counts["load"] == 1


@pytest.mark.asyncio
class TestMonitoringDecorator:
    """Tests for monitoring decorator functionality."""

    async def test_operation_metrics(self):
        """Test operation metrics collection."""
        mock_memory = MockMemory()
        monitoring_memory = MonitoringDecorator(mock_memory)

        # Perform various operations
        await monitoring_memory.store("key1", "value1")
        await monitoring_memory.load("key1")
        await monitoring_memory.load("key2")  # Miss
        await monitoring_memory.delete("key1")
        await monitoring_memory.exists("key1")
        await monitoring_memory.keys()
        await monitoring_memory.clear()
        await monitoring_memory.size()

        metrics = monitoring_memory.get_metrics()

        # Check operation counts
        assert metrics["operations"]["store"]["count"] == 1
        assert metrics["operations"]["load"]["count"] == 2
        assert metrics["operations"]["delete"]["count"] == 1
        assert metrics["operations"]["exists"]["count"] == 1
        assert metrics["operations"]["keys"]["count"] == 1
        assert metrics["operations"]["clear"]["count"] == 1
        assert metrics["operations"]["size"]["count"] == 1

        # Check cache stats
        assert metrics["cache_stats"]["hits"] == 1
        assert metrics["cache_stats"]["misses"] == 1
        assert 0 <= metrics["cache_stats"]["hit_rate"] <= 1

    async def test_error_tracking(self):
        """Test error tracking in monitoring."""
        mock_memory = Mock()
        mock_memory.store = AsyncMock(side_effect=Exception("Store failed"))

        monitoring_memory = MonitoringDecorator(mock_memory)

        # Attempt operation that will fail
        with pytest.raises(Exception):
            await monitoring_memory.store("key1", "value1")

        metrics = monitoring_memory.get_metrics()
        assert metrics["operations"]["store"]["errors"] == 1
        assert len(metrics["errors"]) == 1
        assert "Store failed" in metrics["errors"][0]["error"]

    async def test_slow_operation_tracking(self):
        """Test slow operation tracking."""
        mock_memory = Mock()

        async def slow_load(key, default=None, user_id=None):
            await asyncio.sleep(1.1)  # Simulate slow operation
            return "value"

        mock_memory.load = slow_load

        monitoring_memory = MonitoringDecorator(mock_memory)
        monitoring_memory.slow_threshold = 1.0

        await monitoring_memory.load("key1")

        metrics = monitoring_memory.get_metrics()
        assert len(metrics["slow_operations"]) == 1
        assert metrics["slow_operations"][0]["operation"] == "load"
        assert metrics["slow_operations"][0]["duration"] > 1.0

    async def test_operation_stats(self):
        """Test getting stats for specific operations."""
        mock_memory = MockMemory()
        monitoring_memory = MonitoringDecorator(mock_memory)

        # Perform multiple stores
        for i in range(5):
            await monitoring_memory.store(f"key{i}", f"value{i}")

        stats = monitoring_memory.get_operation_stats("store")
        assert stats["count"] == 5
        assert stats["errors"] == 0
        assert "avg_time" in stats
        assert "error_rate" in stats
        assert stats["error_rate"] == 0


@pytest.mark.asyncio
class TestDecoratorComposition:
    """Tests for composing multiple decorators."""

    async def test_ttl_with_lru(self):
        """Test combining TTL and LRU decorators."""
        mock_memory = MockMemory()

        # Apply TTL first, then LRU with larger capacity to avoid complex eviction issues
        ttl_memory = TTLDecorator(mock_memory, default_ttl=10)
        lru_ttl_memory = LRUDecorator(ttl_memory, max_entries=10)

        # Store entries through the full decorator chain
        await lru_ttl_memory.store("key1", "value1")
        await lru_ttl_memory.store("key2", "value2")

        # Verify TTL is being tracked
        ttl1 = await ttl_memory.get_ttl("key1")
        assert ttl1 is not None and ttl1 > 0

        # Verify LRU is tracking access
        metrics = lru_ttl_memory.get_metrics()
        assert metrics["evictions"] == 0  # No evictions yet

        # Load to update LRU order
        assert await lru_ttl_memory.load("key1") == "value1"
        assert lru_ttl_memory.get_metrics()["hits"] == 1

        # Both decorators are working together successfully
        assert await lru_ttl_memory.load("key2") == "value2"

    async def test_full_stack_decorators(self):
        """Test all decorators working together."""
        mock_memory = MockMemory()

        # Build the full stack
        memory = TTLDecorator(mock_memory, default_ttl=60)
        memory = LRUDecorator(memory, max_entries=100)
        memory = AsyncDecorator(memory)
        memory = MonitoringDecorator(memory)

        # Perform operations
        await memory.store("key1", "value1")
        result = await memory.load("key1")
        assert result == "value1"

        # Check monitoring captured the operations
        metrics = memory.get_metrics()
        assert metrics["operations"]["store"]["count"] == 1
        assert metrics["operations"]["load"]["count"] == 1

    async def test_decorator_order_matters(self):
        """Test that decorator order affects behavior."""
        mock_memory = MockMemory()

        # Monitoring inside LRU - monitors underlying operations
        monitoring_first = MonitoringDecorator(mock_memory)
        lru_outer = LRUDecorator(monitoring_first, max_entries=2)

        await lru_outer.store("key1", "value1")
        await lru_outer.store("key2", "value2")
        await lru_outer.store("key3", "value3")  # Triggers eviction

        # Monitoring should see the eviction delete
        metrics = monitoring_first.get_metrics()
        assert metrics["operations"]["delete"]["count"] > 0  # From eviction
