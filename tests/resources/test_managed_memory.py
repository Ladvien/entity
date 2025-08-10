"""Tests for ManagedMemory lifecycle management functionality."""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.resources import DatabaseResource, VectorStoreResource
from entity.resources.managed_memory import ManagedMemory, MemoryLimitExceeded


@pytest.fixture
def memory_resources():
    """Create test resources for ManagedMemory."""
    infrastructure = DuckDBInfrastructure(":memory:")
    database = DatabaseResource(infrastructure)
    vector_store = VectorStoreResource(infrastructure)
    return database, vector_store


@pytest.fixture
async def managed_memory(memory_resources):
    """Create a test ManagedMemory instance."""
    database, vector_store = memory_resources
    memory = ManagedMemory(
        database=database,
        vector_store=vector_store,
        max_memory_mb=10,  # Small limit for testing
        max_entries_per_user=5,  # Small limit for testing
        cleanup_interval_seconds=1,  # Fast cleanup for testing
        enable_background_cleanup=False,  # Disable for predictable tests
    )
    yield memory
    # Cleanup
    await memory.shutdown()


class TestManagedMemoryBasics:
    """Test basic ManagedMemory functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self, memory_resources):
        """Test ManagedMemory initialization."""
        database, vector_store = memory_resources
        memory = ManagedMemory(
            database=database,
            vector_store=vector_store,
            max_memory_mb=100,
            max_entries_per_user=1000,
        )

        assert memory.max_memory_mb == 100
        assert memory.max_entries_per_user == 1000
        assert memory.cleanup_interval_seconds == 300  # default
        assert memory.memory_pressure_threshold == 0.9  # default

        await memory.shutdown()

    @pytest.mark.asyncio
    async def test_basic_store_and_load(self, managed_memory):
        """Test basic store and load operations."""
        # Store a value
        await managed_memory.store("test_key", "test_value", user_id="user1")

        # Load the value
        result = await managed_memory.load("test_key")
        assert result == "test_value"

        # Check metrics updated
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["total_entries"] == 1
        assert "user1" in metrics["user_metrics"]["entry_counts"]
        assert metrics["user_metrics"]["entry_counts"]["user1"] == 1

    @pytest.mark.asyncio
    async def test_store_with_no_user_id(self, managed_memory):
        """Test storing without user ID."""
        await managed_memory.store("test_key", {"data": "test"})

        result = await managed_memory.load("test_key")
        assert result == {"data": "test"}

        # Should work without user tracking
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["total_entries"] == 1

    @pytest.mark.asyncio
    async def test_delete_functionality(self, managed_memory):
        """Test delete functionality."""
        # Store a value
        await managed_memory.store("delete_test", "value", user_id="user1")

        # Verify it exists
        result = await managed_memory.load("delete_test")
        assert result == "value"

        # Delete it
        deleted = await managed_memory.delete("delete_test")
        assert deleted is True

        # Verify it's gone
        result = await managed_memory.load("delete_test", default="not_found")
        assert result == "not_found"

        # Try to delete non-existent key
        deleted = await managed_memory.delete("non_existent")
        assert deleted is False


class TestTTLFunctionality:
    """Test TTL (Time-To-Live) functionality."""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, managed_memory):
        """Test TTL storage and expiration."""
        # Store with TTL
        await managed_memory.store_with_ttl(
            "ttl_key", "ttl_value", ttl_seconds=1, user_id="user1"
        )

        # Should be available immediately
        result = await managed_memory.load("ttl_key")
        assert result == "ttl_value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired and return default
        result = await managed_memory.load("ttl_key", default="expired")
        assert result == "expired"

        # Check metrics
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["expired_entries_cleaned"] >= 1

    @pytest.mark.asyncio
    async def test_ttl_with_manual_cleanup(self, managed_memory):
        """Test TTL with manual cleanup."""
        # Store multiple TTL entries with longer TTL to prevent auto-expiration
        await managed_memory.store_with_ttl("ttl1", "value1", ttl_seconds=10)
        await managed_memory.store_with_ttl("ttl2", "value2", ttl_seconds=10)

        # Manually set expiry times to past to simulate expiration

        current_time = time.time()
        managed_memory._ttl_registry["ttl1"].expiry_time = current_time - 1
        managed_memory._ttl_registry["ttl2"].expiry_time = current_time - 1

        # Run manual cleanup
        stats = await managed_memory.garbage_collect()

        assert stats["expired_keys_cleaned"] >= 2
        assert stats["total_keys_removed"] >= 2

    @pytest.mark.asyncio
    async def test_ttl_registry_tracking(self, managed_memory):
        """Test TTL registry tracking."""
        # Store with TTL
        await managed_memory.store_with_ttl("ttl_track", "value", ttl_seconds=10)

        # Check TTL registry
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["ttl_entries"] == 1

        # Delete manually
        await managed_memory.delete("ttl_track")

        # TTL registry should be cleaned up
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["ttl_entries"] == 0


class TestLRUEviction:
    """Test LRU (Least Recently Used) eviction functionality."""

    @pytest.mark.asyncio
    async def test_lru_eviction_manual(self, managed_memory):
        """Test manual LRU eviction."""
        # Store multiple entries
        await managed_memory.store("lru1", "value1")
        await asyncio.sleep(0.01)  # Small delay to ensure different access times
        await managed_memory.store("lru2", "value2")
        await asyncio.sleep(0.01)
        await managed_memory.store("lru3", "value3")

        # Access lru2 to make it more recently used
        await managed_memory.load("lru2")

        # Manually evict 2 entries (should evict lru1 and lru3, keeping lru2)
        evicted_keys = await managed_memory._evict_lru_entries(target_count=2)

        assert len(evicted_keys) == 2

        # lru2 should still exist
        result = await managed_memory.load("lru2")
        assert result == "value2"

    @pytest.mark.asyncio
    async def test_lru_tracking_on_access(self, managed_memory):
        """Test that LRU tracking updates on access."""
        # Store entries
        await managed_memory.store("access1", "value1")
        await managed_memory.store("access2", "value2")

        # Access first entry multiple times
        await managed_memory.load("access1")
        await managed_memory.load("access1")
        await managed_memory.load("access2")

        # Check metrics show cache hits
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["cache_hit_rate"] > 0


class TestUserLimits:
    """Test per-user memory limits functionality."""

    @pytest.mark.asyncio
    async def test_user_entry_limits(self, managed_memory):
        """Test per-user entry count limits."""
        user_id = "limited_user"

        # Store up to the limit (5 entries)
        for i in range(5):
            await managed_memory.store(f"user_key_{i}", f"value_{i}", user_id=user_id)

        # Next store should raise exception
        with pytest.raises(MemoryLimitExceeded):
            await managed_memory.store("user_key_6", "value_6", user_id=user_id)

        # Check metrics show violation
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["user_limit_violations"] >= 1
        assert metrics["user_metrics"]["entry_counts"][user_id] == 5

    @pytest.mark.asyncio
    async def test_user_limits_with_ttl(self, managed_memory):
        """Test user limits with TTL entries."""
        user_id = "ttl_user"

        # Store TTL entries up to limit
        for i in range(5):
            await managed_memory.store_with_ttl(
                f"ttl_user_key_{i}", f"value_{i}", ttl_seconds=10, user_id=user_id
            )

        # Should be at limit
        with pytest.raises(MemoryLimitExceeded):
            await managed_memory.store("extra_key", "extra_value", user_id=user_id)

    @pytest.mark.asyncio
    async def test_user_limits_after_deletion(self, managed_memory):
        """Test that user limits are updated after deletion."""
        user_id = "delete_user"

        # Store up to limit
        for i in range(5):
            await managed_memory.store(f"del_key_{i}", f"value_{i}", user_id=user_id)

        # Delete one entry
        await managed_memory.delete("del_key_0")

        # Should be able to store again
        await managed_memory.store("new_key", "new_value", user_id=user_id)

        # Check metrics
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["user_metrics"]["entry_counts"][user_id] == 5


class TestMemoryPressure:
    """Test memory pressure monitoring and handling."""

    @pytest.mark.asyncio
    async def test_memory_pressure_detection(self, managed_memory):
        """Test memory pressure detection and response."""
        # Patch the memory usage method to simulate high usage
        with patch.object(managed_memory, "_get_memory_usage_mb", return_value=9.5):
            # This should trigger memory pressure (95% of 10MB limit)
            await managed_memory.store("pressure_test", "x" * 1000)

            metrics = await managed_memory.get_memory_metrics()
            # Memory pressure should be detected
            assert metrics["memory_pressure"] > managed_memory.memory_pressure_threshold

    @pytest.mark.asyncio
    async def test_automatic_eviction_on_pressure(self, managed_memory):
        """Test automatic eviction when memory pressure is high."""
        # Store several entries
        for i in range(10):
            await managed_memory.store(f"pressure_key_{i}", "x" * 100)

        initial_count = len(managed_memory._access_times)

        # Simulate high memory pressure
        with patch.object(managed_memory, "_get_memory_usage_mb", return_value=9.5):
            await managed_memory._check_memory_pressure(additional_bytes=1024)

        # Should have evicted some entries
        final_count = len(managed_memory._access_times)
        assert final_count < initial_count

        # Check metrics
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["memory_pressure_events"] >= 1


class TestGarbageCollection:
    """Test garbage collection functionality."""

    @pytest.mark.asyncio
    async def test_manual_garbage_collection(self, managed_memory):
        """Test manual garbage collection."""
        # Store some regular entries
        await managed_memory.store("gc_test_1", "value1")
        await managed_memory.store("gc_test_2", "value2")

        # Store TTL entries with long TTL to prevent auto-expiration
        await managed_memory.store_with_ttl("gc_ttl_1", "ttl_value1", ttl_seconds=10)
        await managed_memory.store_with_ttl("gc_ttl_2", "ttl_value2", ttl_seconds=10)

        # Manually expire the TTL entries

        current_time = time.time()
        managed_memory._ttl_registry["gc_ttl_1"].expiry_time = current_time - 1
        managed_memory._ttl_registry["gc_ttl_2"].expiry_time = current_time - 1

        # Run garbage collection
        stats = await managed_memory.garbage_collect()

        assert stats["expired_keys_cleaned"] >= 2
        assert stats["total_keys_removed"] >= 2
        assert "time_taken_ms" in stats
        assert stats["time_taken_ms"] >= 0

    @pytest.mark.asyncio
    async def test_gc_with_memory_pressure(self, managed_memory):
        """Test garbage collection under memory pressure."""
        # Store many entries to create pressure
        for i in range(10):
            await managed_memory.store(f"gc_pressure_{i}", "x" * 100)

        # Simulate high memory usage
        with patch.object(managed_memory, "_get_memory_usage_mb", return_value=9.5):
            stats = await managed_memory.garbage_collect()

            # Should have performed LRU eviction
            assert stats["lru_evictions"] > 0


class TestMetrics:
    """Test comprehensive metrics functionality."""

    @pytest.mark.asyncio
    async def test_comprehensive_metrics(self, managed_memory):
        """Test comprehensive metrics collection."""
        # Store various types of entries
        await managed_memory.store("metric_test_1", "value1", user_id="user1")
        await managed_memory.store_with_ttl(
            "ttl_metric", "ttl_val", ttl_seconds=10, user_id="user2"
        )

        # Access some entries
        await managed_memory.load("metric_test_1")
        await managed_memory.load("nonexistent", default="default")

        # Get metrics
        metrics = await managed_memory.get_memory_metrics()

        # Check all required fields are present
        required_fields = [
            "total_entries",
            "total_size_mb",
            "memory_limit_mb",
            "memory_pressure",
            "expired_entries_cleaned",
            "lru_evictions",
            "garbage_collections_run",
            "memory_pressure_events",
            "user_limit_violations",
            "cache_hit_rate",
            "user_metrics",
            "ttl_entries",
            "cleanup_config",
        ]

        for field in required_fields:
            assert field in metrics, f"Missing metric field: {field}"

        # Check user metrics structure
        assert "entry_counts" in metrics["user_metrics"]
        assert "size_bytes" in metrics["user_metrics"]

        # Check cleanup config
        config = metrics["cleanup_config"]
        assert config["max_memory_mb"] == 10
        assert config["max_entries_per_user"] == 5

    @pytest.mark.asyncio
    async def test_metrics_reset(self, managed_memory):
        """Test metrics reset functionality."""
        # Generate some metrics
        await managed_memory.store("reset_test", "value")
        await managed_memory.load("reset_test")
        await managed_memory.garbage_collect()

        # Check metrics exist
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["total_entries"] > 0
        assert metrics["garbage_collections_run"] > 0

        # Reset metrics
        await managed_memory.reset_metrics()

        # Check metrics are reset (but entries remain)
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["garbage_collections_run"] == 0
        assert metrics["cache_hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_user_metrics_tracking(self, managed_memory):
        """Test detailed user metrics tracking."""
        # Store entries for multiple users
        await managed_memory.store("user1_key1", "value1", user_id="user1")
        await managed_memory.store("user1_key2", "value2", user_id="user1")
        await managed_memory.store("user2_key1", "value3", user_id="user2")

        metrics = await managed_memory.get_memory_metrics()

        # Check user entry counts
        assert metrics["user_metrics"]["entry_counts"]["user1"] == 2
        assert metrics["user_metrics"]["entry_counts"]["user2"] == 1

        # Check user size tracking
        assert "user1" in metrics["user_metrics"]["size_bytes"]
        assert "user2" in metrics["user_metrics"]["size_bytes"]
        assert metrics["user_metrics"]["size_bytes"]["user1"] > 0
        assert metrics["user_metrics"]["size_bytes"]["user2"] > 0


class TestBackgroundCleanup:
    """Test background cleanup functionality."""

    @pytest.mark.asyncio
    async def test_background_cleanup_disabled(self, managed_memory):
        """Test that background cleanup can be disabled."""
        # Our fixture has background cleanup disabled
        assert managed_memory.enable_background_cleanup is False
        assert managed_memory._cleanup_task is None

    @pytest.mark.asyncio
    async def test_background_cleanup_enabled(self, memory_resources):
        """Test background cleanup when enabled."""
        database, vector_store = memory_resources
        memory = ManagedMemory(
            database=database,
            vector_store=vector_store,
            cleanup_interval_seconds=0.1,  # Very fast for testing
            enable_background_cleanup=True,
        )

        try:
            # Background task should be running
            assert memory._cleanup_task is not None
            assert not memory._cleanup_task.done()

            # Store TTL entry that expires quickly
            await memory.store_with_ttl("bg_ttl", "value", ttl_seconds=0.1)

            # Wait for background cleanup
            await asyncio.sleep(0.3)

            # Entry should be cleaned up
            result = await memory.load("bg_ttl", default="cleaned")
            assert result == "cleaned"

        finally:
            await memory.shutdown()

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self, memory_resources):
        """Test background cleanup error handling."""
        database, vector_store = memory_resources
        memory = ManagedMemory(
            database=database,
            vector_store=vector_store,
            cleanup_interval_seconds=0.1,
            enable_background_cleanup=True,
        )

        # Mock garbage_collect to raise an exception
        original_gc = memory.garbage_collect
        memory.garbage_collect = AsyncMock(side_effect=Exception("Test error"))

        try:
            # Wait for background cleanup to run and handle error
            await asyncio.sleep(0.2)

            # Background task should still be running despite error
            assert not memory._cleanup_task.done()

        finally:
            memory.garbage_collect = original_gc
            await memory.shutdown()


class TestShutdown:
    """Test graceful shutdown functionality."""

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, memory_resources):
        """Test graceful shutdown process."""
        database, vector_store = memory_resources
        memory = ManagedMemory(
            database=database,
            vector_store=vector_store,
            enable_background_cleanup=True,
        )

        # Store some data
        await memory.store("shutdown_test", "value")

        # Shutdown should complete without errors
        await memory.shutdown()

        # Background task should be cancelled
        assert memory._cleanup_task.done() or memory._cleanup_task.cancelled()

    @pytest.mark.asyncio
    async def test_shutdown_runs_final_cleanup(self, memory_resources):
        """Test that shutdown runs final cleanup."""
        database, vector_store = memory_resources
        memory = ManagedMemory(
            database=database,
            vector_store=vector_store,
            enable_background_cleanup=False,
        )

        # Store TTL entries
        await memory.store_with_ttl("final_ttl_1", "value1", ttl_seconds=0.1)
        await memory.store_with_ttl("final_ttl_2", "value2", ttl_seconds=0.1)

        # Wait for expiration
        await asyncio.sleep(0.2)

        initial_gc_count = memory._metrics.garbage_collections_run

        # Shutdown should run final cleanup
        await memory.shutdown()

        # Should have run garbage collection
        assert memory._metrics.garbage_collections_run > initial_gc_count


class TestIntegration:
    """Integration tests for complete ManagedMemory workflow."""

    @pytest.mark.asyncio
    async def test_complete_lifecycle_workflow(self, managed_memory):
        """Test complete memory lifecycle workflow."""
        # Store regular entries
        await managed_memory.store("lifecycle_1", "value1", user_id="test_user")
        await managed_memory.store(
            "lifecycle_2", {"key": "value2"}, user_id="test_user"
        )

        # Store TTL entries
        await managed_memory.store_with_ttl(
            "ttl_lifecycle", "ttl_value", ttl_seconds=10, user_id="test_user"
        )

        # Manually expire for predictable testing

        managed_memory._ttl_registry["ttl_lifecycle"].expiry_time = time.time() - 1

        # Access entries to update LRU
        result1 = await managed_memory.load("lifecycle_1")
        assert result1 == "value1"

        result2 = await managed_memory.load("lifecycle_2")
        assert result2 == {"key": "value2"}

        # Check initial metrics
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["total_entries"] == 3
        assert metrics["user_metrics"]["entry_counts"]["test_user"] == 3
        assert metrics["ttl_entries"] == 1

        # Access expired entry (should be cleaned up automatically)
        expired_result = await managed_memory.load("ttl_lifecycle", default="expired")
        assert expired_result == "expired"

        # Run garbage collection - the expired entry should already be cleaned by load()
        await managed_memory.garbage_collect()
        # Note: expired entry was likely already cleaned during load() call

        # Check final metrics
        final_metrics = await managed_memory.get_memory_metrics()
        assert final_metrics["total_entries"] == 2  # Regular entries remain
        assert final_metrics["expired_entries_cleaned"] >= 1
        assert final_metrics["ttl_entries"] == 0  # TTL entry cleaned up

    @pytest.mark.asyncio
    async def test_high_load_scenario(self, managed_memory):
        """Test ManagedMemory under high load conditions."""
        # Store entries sequentially to ensure user limits are properly enforced
        results = []

        for i in range(30):  # Smaller number for reliability
            user_id = f"user_{i%2}"  # Use only 2 users

            try:
                if i % 3 == 0:
                    # Some with TTL
                    await managed_memory.store_with_ttl(
                        f"load_ttl_{i}", f"value_{i}", ttl_seconds=10, user_id=user_id
                    )
                else:
                    # Some regular
                    await managed_memory.store(
                        f"load_key_{i}", f"value_{i}", user_id=user_id
                    )
                results.append("success")
            except MemoryLimitExceeded:
                results.append("limit_exceeded")

        # Some should succeed, some should fail due to user limits
        successes = sum(1 for r in results if r == "success")
        failures = sum(1 for r in results if r == "limit_exceeded")

        assert successes > 0
        assert (
            failures > 0
        )  # Should hit user limits (30 entries / 2 users = 15 per user > 5 limit)

        # Manually expire some TTL entries for testing

        current_time = time.time()
        expired_count = 0
        for key in list(managed_memory._ttl_registry.keys()):
            if "load_ttl_" in key and expired_count < 3:  # Expire a few entries
                managed_memory._ttl_registry[key].expiry_time = current_time - 1
                expired_count += 1

        # Run cleanup
        gc_stats = await managed_memory.garbage_collect()

        # Should have cleaned up expired entries (if any existed)
        if expired_count > 0:
            assert gc_stats["expired_keys_cleaned"] >= expired_count

        # Final metrics should be consistent
        metrics = await managed_memory.get_memory_metrics()
        assert metrics["user_limit_violations"] > 0
        assert metrics["expired_entries_cleaned"] > 0
