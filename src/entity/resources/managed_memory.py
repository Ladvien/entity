"""Managed memory resource with lifecycle management capabilities.

This module provides the ManagedMemory class that extends the base Memory
resource with advanced lifecycle management features including TTL (Time-To-Live),
LRU (Least Recently Used) eviction, memory pressure monitoring, and automatic
garbage collection.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from entity.resources.logging import LogCategory, LogLevel
from entity.resources.memory import Memory


@dataclass
class MemoryMetrics:
    """Memory usage and performance metrics."""

    total_entries: int = 0
    total_size_bytes: int = 0
    expired_entries_cleaned: int = 0
    lru_evictions: int = 0
    garbage_collections_run: int = 0
    memory_pressure_events: int = 0
    user_limit_violations: int = 0
    average_access_time_ms: float = 0.0
    cache_hit_rate: float = 0.0

    user_entry_counts: Dict[str, int] = field(default_factory=dict)
    user_size_bytes: Dict[str, int] = field(default_factory=dict)


@dataclass
class TTLEntry:
    """TTL registry entry with expiration metadata."""

    key: str
    expiry_time: float
    user_id: Optional[str] = None


class ManagedMemory(Memory):
    """Extended Memory with lifecycle management capabilities.

    This class provides automatic memory cleanup through TTL expiration,
    LRU eviction policies, memory pressure monitoring, and comprehensive
    metrics collection. It maintains backward compatibility with the base
    Memory class while adding advanced management features.

    Key Features:
    - TTL support for automatic entry expiration
    - LRU eviction policy for memory pressure relief
    - Per-user memory usage limits and tracking
    - Memory pressure monitoring and alerts
    - Manual and automatic garbage collection
    - Comprehensive metrics and monitoring
    - Configurable cleanup policies

    Args:
        database: Database resource for structured data storage
        vector_store: Vector store resource for semantic search
        max_memory_mb: Maximum memory limit in MB (default: 1000)
        max_entries_per_user: Maximum entries per user (default: 10000)
        cleanup_interval_seconds: Background cleanup interval (default: 300)
        memory_pressure_threshold: Threshold for pressure alerts (default: 0.9)
        enable_background_cleanup: Enable automatic background cleanup (default: True)
    """

    def __init__(
        self,
        database,
        vector_store,
        max_memory_mb: int = 1000,
        max_entries_per_user: int = 10000,
        cleanup_interval_seconds: int = 300,
        memory_pressure_threshold: float = 0.9,
        enable_background_cleanup: bool = True,
    ) -> None:
        """Initialize ManagedMemory with lifecycle management capabilities."""
        super().__init__(database, vector_store)

        self.max_memory_mb = max_memory_mb
        self.max_entries_per_user = max_entries_per_user
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.memory_pressure_threshold = memory_pressure_threshold
        self.enable_background_cleanup = enable_background_cleanup

        self._ttl_registry: Dict[str, TTLEntry] = {}
        self._access_times: OrderedDict[str, float] = OrderedDict()
        self._entry_sizes: Dict[str, int] = {}
        self._user_keys: Dict[str, Set[str]] = {}

        self._metrics = MemoryMetrics()
        self._last_cleanup = time.time()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._access_count = 0
        self._hit_count = 0
        self._expiry_tasks: Dict[str, asyncio.Task] = {}

        if self.enable_background_cleanup:
            self._cleanup_task = asyncio.create_task(self._background_cleanup_loop())

    async def store_with_ttl(
        self, key: str, value: Any, ttl_seconds: int, user_id: Optional[str] = None
    ) -> None:
        """Store a value with automatic expiration after TTL seconds.

        Args:
            key: Storage key for the value
            value: Value to store (will be JSON serialized)
            ttl_seconds: Time-to-live in seconds
            user_id: Optional user ID for tracking and limits
        """
        if user_id and not await self._check_user_limits(user_id):
            self._metrics.user_limit_violations += 1
            raise MemoryLimitExceeded(
                f"User {user_id} has exceeded memory limits "
                f"({self.max_entries_per_user} entries max)"
            )

        await self.store(key, value, user_id=user_id)

        expiry_time = time.time() + ttl_seconds
        self._ttl_registry[key] = TTLEntry(
            key=key, expiry_time=expiry_time, user_id=user_id
        )

        expiry_task = asyncio.create_task(self._expire_after(key, ttl_seconds))
        self._expiry_tasks[key] = expiry_task

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with optional user tracking.

        Args:
            key: Storage key
            value: Value to store
            user_id: Optional user ID for tracking and limits
        """
        if user_id and not await self._check_user_limits(user_id):
            self._metrics.user_limit_violations += 1
            raise MemoryLimitExceeded(f"User {user_id} has exceeded memory limits")

        serialized = json.dumps(value)
        entry_size = len(serialized.encode("utf-8"))

        await self._check_memory_pressure(entry_size)

        await super().store(key, value)

        current_time = time.time()
        self._access_times[key] = current_time
        self._entry_sizes[key] = entry_size

        if user_id:
            if user_id not in self._user_keys:
                self._user_keys[user_id] = set()
            self._user_keys[user_id].add(key)

            self._metrics.user_entry_counts[user_id] = len(self._user_keys[user_id])
            self._metrics.user_size_bytes[user_id] = sum(
                self._entry_sizes.get(k, 0) for k in self._user_keys[user_id]
            )

        self._metrics.total_entries = len(self._access_times)
        self._metrics.total_size_bytes = sum(self._entry_sizes.values())

    async def load(self, key: str, default: Any | None = None) -> Any:
        """Load a value and update access tracking.

        Args:
            key: Storage key
            default: Default value if key doesn't exist

        Returns:
            Stored value or default
        """
        self._access_count += 1

        if key in self._ttl_registry:
            if time.time() > self._ttl_registry[key].expiry_time:
                await self._remove_expired_key(key)
                return default

        result = await super().load(key, default)

        if result == default:
            return default

        current_time = time.time()
        if key in self._access_times:
            self._access_times.move_to_end(key)
            self._hit_count += 1
        self._access_times[key] = current_time

        self._metrics.cache_hit_rate = (self._hit_count / self._access_count) * 100

        return result

    async def delete(self, key: str) -> bool:
        """Delete a key and update tracking.

        Args:
            key: Key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        exists = await self.load(key) is not None
        if not exists:
            return False

        await self._execute_with_locks("DELETE FROM memory WHERE key = ?", key)

        await self._cleanup_key_tracking(key)

        return True

    async def garbage_collect(self) -> Dict[str, int]:
        """Manually run garbage collection and return statistics.

        Returns:
            Dictionary with cleanup statistics
        """
        start_time = time.time()
        stats = {
            "expired_keys_cleaned": 0,
            "lru_evictions": 0,
            "total_keys_removed": 0,
            "time_taken_ms": 0,
        }

        expired_keys = await self._cleanup_expired_keys()
        stats["expired_keys_cleaned"] = len(expired_keys)

        memory_usage = await self._get_memory_usage_mb()
        if memory_usage > self.max_memory_mb * self.memory_pressure_threshold:
            evicted_keys = await self._evict_lru_entries()
            stats["lru_evictions"] = len(evicted_keys)

        stats["total_keys_removed"] = (
            stats["expired_keys_cleaned"] + stats["lru_evictions"]
        )
        stats["time_taken_ms"] = (time.time() - start_time) * 1000

        self._metrics.expired_entries_cleaned += stats["expired_keys_cleaned"]
        self._metrics.lru_evictions += stats["lru_evictions"]
        self._metrics.garbage_collections_run += 1

        return stats

    async def get_memory_metrics(self) -> Dict[str, Any]:
        """Get comprehensive memory usage metrics.

        Returns:
            Dictionary containing detailed memory metrics
        """
        current_memory_mb = await self._get_memory_usage_mb()
        memory_pressure = current_memory_mb / self.max_memory_mb

        if self._access_count > 0:
            self._metrics.average_access_time_ms = 1.0

        return {
            "total_entries": self._metrics.total_entries,
            "total_size_mb": current_memory_mb,
            "memory_limit_mb": self.max_memory_mb,
            "memory_pressure": round(memory_pressure, 3),
            "expired_entries_cleaned": self._metrics.expired_entries_cleaned,
            "lru_evictions": self._metrics.lru_evictions,
            "garbage_collections_run": self._metrics.garbage_collections_run,
            "memory_pressure_events": self._metrics.memory_pressure_events,
            "user_limit_violations": self._metrics.user_limit_violations,
            "cache_hit_rate": round(self._metrics.cache_hit_rate, 2),
            "user_metrics": {
                "entry_counts": dict(self._metrics.user_entry_counts),
                "size_bytes": dict(self._metrics.user_size_bytes),
            },
            "ttl_entries": len(self._ttl_registry),
            "cleanup_config": {
                "max_memory_mb": self.max_memory_mb,
                "max_entries_per_user": self.max_entries_per_user,
                "cleanup_interval_seconds": self.cleanup_interval_seconds,
                "memory_pressure_threshold": self.memory_pressure_threshold,
            },
        }

    async def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self._metrics = MemoryMetrics()
        self._access_count = 0
        self._hit_count = 0

    async def _expire_after(self, key: str, ttl_seconds: int) -> None:
        """Automatically expire a key after TTL seconds."""
        try:
            await asyncio.sleep(ttl_seconds)

            if key in self._ttl_registry:
                entry = self._ttl_registry[key]
                if time.time() >= entry.expiry_time:
                    await self._remove_expired_key(key)
        except asyncio.CancelledError:
            pass
        finally:
            self._expiry_tasks.pop(key, None)

    async def _remove_expired_key(self, key: str) -> None:
        """Remove an expired key and update tracking."""
        await self._execute_with_locks("DELETE FROM memory WHERE key = ?", key)

        await self._cleanup_key_tracking(key)

        self._metrics.expired_entries_cleaned += 1

    async def _cleanup_key_tracking(self, key: str) -> None:
        """Clean up all tracking structures for a key."""
        user_id = None
        if key in self._ttl_registry:
            user_id = self._ttl_registry[key].user_id
            del self._ttl_registry[key]
        else:
            for uid, keys in self._user_keys.items():
                if key in keys:
                    user_id = uid
                    break

        if key in self._expiry_tasks:
            task = self._expiry_tasks[key]
            if not task.done():
                task.cancel()
            del self._expiry_tasks[key]

        if user_id and user_id in self._user_keys:
            self._user_keys[user_id].discard(key)

            self._metrics.user_entry_counts[user_id] = len(self._user_keys[user_id])
            self._metrics.user_size_bytes[user_id] = sum(
                self._entry_sizes.get(k, 0) for k in self._user_keys[user_id]
            )

        self._access_times.pop(key, None)

        self._entry_sizes.pop(key, None)

        self._metrics.total_entries = len(self._access_times)
        self._metrics.total_size_bytes = sum(self._entry_sizes.values())

    async def _cleanup_expired_keys(self) -> List[str]:
        """Clean up all expired keys and return the list of cleaned keys."""
        current_time = time.time()
        expired_keys = []

        for key, entry in list(self._ttl_registry.items()):
            if current_time >= entry.expiry_time:
                expired_keys.append(key)

        for key in expired_keys:
            await self._remove_expired_key(key)

        return expired_keys

    async def _evict_lru_entries(self, target_count: Optional[int] = None) -> List[str]:
        """Evict least recently used entries to free memory.

        Args:
            target_count: Number of entries to evict (default: 10% of entries)

        Returns:
            List of evicted keys
        """
        if not self._access_times:
            return []

        if target_count is None:
            target_count = max(1, len(self._access_times) // 10)

        evicted_keys = []

        for _ in range(min(target_count, len(self._access_times))):
            if not self._access_times:
                break

            lru_key = next(iter(self._access_times))

            await self._execute_with_locks("DELETE FROM memory WHERE key = ?", lru_key)

            await self._cleanup_key_tracking(lru_key)

            evicted_keys.append(lru_key)

        return evicted_keys

    async def _check_user_limits(self, user_id: str) -> bool:
        """Check if user is within memory limits.

        Args:
            user_id: User ID to check

        Returns:
            True if within limits, False otherwise
        """
        if user_id not in self._user_keys:
            return True

        user_entry_count = len(self._user_keys[user_id])
        return user_entry_count < self.max_entries_per_user

    async def _check_memory_pressure(self, additional_bytes: int = 0) -> None:
        """Check for memory pressure and trigger cleanup if needed.

        Args:
            additional_bytes: Additional bytes that will be added
        """
        current_usage_mb = await self._get_memory_usage_mb()
        projected_usage_mb = current_usage_mb + (additional_bytes / (1024 * 1024))

        pressure_ratio = projected_usage_mb / self.max_memory_mb

        if pressure_ratio > self.memory_pressure_threshold:
            self._metrics.memory_pressure_events += 1

            await self._evict_lru_entries(
                target_count=max(10, len(self._access_times) // 5)
            )

    async def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB.

        Returns:
            Current memory usage in megabytes
        """
        total_bytes = sum(self._entry_sizes.values())
        return total_bytes / (1024 * 1024)

    async def _background_cleanup_loop(self) -> None:
        """Background task for periodic cleanup operations."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)

                await self.garbage_collect()

                self._last_cleanup = time.time()

            except asyncio.CancelledError:
                break
            except Exception as e:
                if hasattr(self, "resources") and "logging" in self.resources:
                    await self.resources["logging"].log(
                        LogLevel.ERROR,
                        LogCategory.SYSTEM,
                        f"Background cleanup error: {e}",
                        exception=str(e),
                    )

    async def shutdown(self) -> None:
        """Gracefully shutdown managed memory and cleanup tasks."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        for task in self._expiry_tasks.values():
            if not task.done():
                task.cancel()

        if self._expiry_tasks:
            await asyncio.gather(*self._expiry_tasks.values(), return_exceptions=True)

        self._expiry_tasks.clear()

        await self.garbage_collect()


class MemoryLimitExceeded(Exception):
    """Exception raised when memory limits are exceeded."""

    pass
