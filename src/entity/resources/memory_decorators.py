"""Memory feature decorators for adding TTL, LRU, locking, async, and monitoring capabilities."""

from __future__ import annotations

import asyncio
import fcntl
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from entity.resources.memory_components import IMemory, MemoryDecorator


@dataclass
class TTLEntry:
    """Entry with time-to-live information."""

    expiry_time: float
    key: str
    user_id: Optional[str] = None


class TTLDecorator(MemoryDecorator):
    """Decorator that adds time-to-live (TTL) functionality to memory.

    Keys can be set to automatically expire after a certain duration.
    """

    def __init__(
        self,
        memory: IMemory,
        default_ttl: Optional[int] = None,
        cleanup_interval: int = 60,
    ):
        """Initialize TTL decorator.

        Args:
            memory: The memory instance to wrap
            default_ttl: Default TTL in seconds for all keys (None = no expiry)
            cleanup_interval: Interval in seconds between cleanup runs
        """
        super().__init__(memory)
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self._ttl_entries: Dict[str, TTLEntry] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Start background cleanup task
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        try:
            asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        except RuntimeError:
            # No event loop running, skip cleanup task
            pass

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue cleanup loop
                pass

    async def _cleanup_expired(self) -> List[str]:
        """Remove expired entries from memory."""
        current_time = time.time()
        expired_keys = []

        async with self._lock:
            # Find expired entries
            for key, entry in list(self._ttl_entries.items()):
                if entry.expiry_time <= current_time:
                    expired_keys.append(key)
                    # Delete from underlying memory
                    await self._memory.delete(entry.key, entry.user_id)
                    # Remove from TTL tracking
                    del self._ttl_entries[key]

        return expired_keys

    async def store_with_ttl(
        self, key: str, value: Any, ttl: int, user_id: Optional[str] = None
    ) -> None:
        """Store a value with specific TTL.

        Args:
            key: The key to store
            value: The value to store
            ttl: Time-to-live in seconds
            user_id: Optional user ID for scoping
        """
        await self._memory.store(key, value, user_id)

        # Track TTL
        expiry_time = time.time() + ttl
        tracking_key = f"{user_id}:{key}" if user_id else key

        async with self._lock:
            self._ttl_entries[tracking_key] = TTLEntry(
                expiry_time=expiry_time, key=key, user_id=user_id
            )

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with default TTL if configured."""
        # Ensure cleanup task is started if we have an event loop now
        if self._cleanup_task is None:
            self._start_cleanup_task()

        if self.default_ttl:
            await self.store_with_ttl(key, value, self.default_ttl, user_id)
        else:
            await self._memory.store(key, value, user_id)

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value, returning default if expired."""
        tracking_key = f"{user_id}:{key}" if user_id else key

        # Check if key has TTL and is expired
        async with self._lock:
            if tracking_key in self._ttl_entries:
                entry = self._ttl_entries[tracking_key]
                if entry.expiry_time <= time.time():
                    # Expired - delete it
                    await self._memory.delete(key, user_id)
                    del self._ttl_entries[tracking_key]
                    return default

        return await self._memory.load(key, default, user_id)

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key and its TTL tracking."""
        tracking_key = f"{user_id}:{key}" if user_id else key

        async with self._lock:
            if tracking_key in self._ttl_entries:
                del self._ttl_entries[tracking_key]

        return await self._memory.delete(key, user_id)

    async def get_ttl(self, key: str, user_id: Optional[str] = None) -> Optional[int]:
        """Get remaining TTL for a key in seconds.

        Returns:
            Remaining TTL in seconds, or None if no TTL set
        """
        tracking_key = f"{user_id}:{key}" if user_id else key

        async with self._lock:
            if tracking_key in self._ttl_entries:
                entry = self._ttl_entries[tracking_key]
                remaining = entry.expiry_time - time.time()
                return max(0, int(remaining))

        return None

    async def shutdown(self) -> None:
        """Shutdown the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class LRUDecorator(MemoryDecorator):
    """Decorator that adds Least Recently Used (LRU) eviction to memory.

    Automatically evicts least recently used items when capacity is reached.
    """

    def __init__(
        self, memory: IMemory, max_entries: int = 1000, evict_count: int = 100
    ):
        """Initialize LRU decorator.

        Args:
            memory: The memory instance to wrap
            max_entries: Maximum number of entries before eviction
            evict_count: Number of entries to evict when max is reached
        """
        super().__init__(memory)
        self.max_entries = max_entries
        self.evict_count = evict_count
        self._access_order: OrderedDict[str, datetime] = OrderedDict()
        self._lock = asyncio.Lock()
        self._metrics = {"hits": 0, "misses": 0, "evictions": 0}

    async def _track_access(self, key: str, user_id: Optional[str] = None) -> None:
        """Track access to a key for LRU ordering."""
        tracking_key = f"{user_id}:{key}" if user_id else key

        async with self._lock:
            # Move to end (most recently used)
            if tracking_key in self._access_order:
                self._access_order.move_to_end(tracking_key)
            else:
                self._access_order[tracking_key] = datetime.now()

    async def _evict_lru(self) -> List[str]:
        """Evict least recently used entries."""
        evicted = []

        async with self._lock:
            # Get least recently used keys
            for _ in range(min(self.evict_count, len(self._access_order))):
                if not self._access_order:
                    break

                tracking_key, _ = self._access_order.popitem(last=False)

                # Parse user_id and key
                if ":" in tracking_key:
                    user_id, key = tracking_key.split(":", 1)
                else:
                    user_id, key = None, tracking_key

                # Delete from underlying memory
                await self._memory.delete(key, user_id)
                evicted.append(tracking_key)
                self._metrics["evictions"] += 1

        return evicted

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value, evicting LRU entries if needed."""
        # Check if eviction is needed
        if len(self._access_order) >= self.max_entries:
            await self._evict_lru()

        await self._memory.store(key, value, user_id)
        await self._track_access(key, user_id)

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value, tracking access for LRU."""
        value = await self._memory.load(key, default, user_id)

        if value is not default:
            await self._track_access(key, user_id)
            self._metrics["hits"] += 1
        else:
            self._metrics["misses"] += 1

        return value

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key and remove from LRU tracking."""
        tracking_key = f"{user_id}:{key}" if user_id else key

        async with self._lock:
            if tracking_key in self._access_order:
                del self._access_order[tracking_key]

        return await self._memory.delete(key, user_id)

    def get_metrics(self) -> Dict[str, int]:
        """Get LRU metrics."""
        return self._metrics.copy()


class LockingDecorator(MemoryDecorator):
    """Decorator that adds process-safe locking to memory operations.

    Ensures thread and process safety for memory operations.
    """

    def __init__(
        self,
        memory: IMemory,
        lock_dir: str = "/tmp/entity_locks",
        timeout: float = 10.0,
    ):
        """Initialize locking decorator.

        Args:
            memory: The memory instance to wrap
            lock_dir: Directory for lock files
            timeout: Lock acquisition timeout in seconds
        """
        super().__init__(memory)
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True)
        self.timeout = timeout
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_files: Dict[str, Any] = {}
        self._metrics = {"acquisitions": 0, "timeouts": 0, "contentions": 0}

    def _get_lock_path(self, key: str) -> Path:
        """Get lock file path for a key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = str(hash(key) % 10000000)
        return self.lock_dir / f"lock_{key_hash}.lock"

    async def _acquire_lock(self, key: str) -> None:
        """Acquire both async and file-based lock for a key."""
        # Get or create async lock
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        # Acquire async lock
        start_time = time.time()
        try:
            await asyncio.wait_for(self._locks[key].acquire(), timeout=self.timeout)
        except asyncio.TimeoutError:
            self._metrics["timeouts"] += 1
            raise TimeoutError(f"Failed to acquire lock for key {key}")

        wait_time = time.time() - start_time
        if wait_time > 0.01:  # Contention if waited more than 10ms
            self._metrics["contentions"] += 1
        self._metrics["acquisitions"] += 1

        # Acquire file lock for cross-process safety
        lock_path = self._get_lock_path(key)
        lock_file = await asyncio.to_thread(open, str(lock_path), "w")
        await asyncio.to_thread(fcntl.flock, lock_file, fcntl.LOCK_EX)
        self._lock_files[key] = lock_file

    async def _release_lock(self, key: str) -> None:
        """Release both async and file-based lock for a key."""
        # Release file lock
        if key in self._lock_files:
            lock_file = self._lock_files[key]
            await asyncio.to_thread(fcntl.flock, lock_file, fcntl.LOCK_UN)
            lock_file.close()
            del self._lock_files[key]

        # Release async lock
        if key in self._locks:
            self._locks[key].release()

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with locking."""
        lock_key = f"{user_id}:{key}" if user_id else key

        await self._acquire_lock(lock_key)
        try:
            await self._memory.store(key, value, user_id)
        finally:
            await self._release_lock(lock_key)

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value with locking."""
        lock_key = f"{user_id}:{key}" if user_id else key

        await self._acquire_lock(lock_key)
        try:
            return await self._memory.load(key, default, user_id)
        finally:
            await self._release_lock(lock_key)

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key with locking."""
        lock_key = f"{user_id}:{key}" if user_id else key

        await self._acquire_lock(lock_key)
        try:
            return await self._memory.delete(key, user_id)
        finally:
            await self._release_lock(lock_key)

    def get_metrics(self) -> Dict[str, int]:
        """Get locking metrics."""
        return self._metrics.copy()


class AsyncDecorator(MemoryDecorator):
    """Decorator that adds async capabilities to synchronous memory implementations.

    Converts sync operations to async using thread pool executor.
    """

    def __init__(self, memory: IMemory, max_workers: int = 10):
        """Initialize async decorator.

        Args:
            memory: The memory instance to wrap
            max_workers: Maximum number of worker threads
        """
        super().__init__(memory)
        self.max_workers = max_workers
        # Note: In real implementation, would use ThreadPoolExecutor
        # For now, we'll use asyncio.to_thread which is simpler

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value asynchronously."""
        # If the wrapped memory already has async methods, use them
        if asyncio.iscoroutinefunction(self._memory.store):
            await self._memory.store(key, value, user_id)
        else:
            # Convert sync to async
            await asyncio.to_thread(self._memory.store, key, value, user_id)

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value asynchronously."""
        if asyncio.iscoroutinefunction(self._memory.load):
            return await self._memory.load(key, default, user_id)
        else:
            return await asyncio.to_thread(self._memory.load, key, default, user_id)

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key asynchronously."""
        if asyncio.iscoroutinefunction(self._memory.delete):
            return await self._memory.delete(key, user_id)
        else:
            return await asyncio.to_thread(self._memory.delete, key, user_id)

    async def exists(self, key: str, user_id: Optional[str] = None) -> bool:
        """Check if key exists asynchronously."""
        if asyncio.iscoroutinefunction(self._memory.exists):
            return await self._memory.exists(key, user_id)
        else:
            return await asyncio.to_thread(self._memory.exists, key, user_id)

    async def keys(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[str]:
        """Get keys asynchronously."""
        if asyncio.iscoroutinefunction(self._memory.keys):
            return await self._memory.keys(pattern, user_id)
        else:
            return await asyncio.to_thread(self._memory.keys, pattern, user_id)

    async def clear(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> int:
        """Clear keys asynchronously."""
        if asyncio.iscoroutinefunction(self._memory.clear):
            return await self._memory.clear(pattern, user_id)
        else:
            return await asyncio.to_thread(self._memory.clear, pattern, user_id)

    async def size(self, user_id: Optional[str] = None) -> int:
        """Get size asynchronously."""
        if asyncio.iscoroutinefunction(self._memory.size):
            return await self._memory.size(user_id)
        else:
            return await asyncio.to_thread(self._memory.size, user_id)


class MonitoringDecorator(MemoryDecorator):
    """Decorator that adds monitoring and metrics collection to memory operations.

    Tracks operation counts, latencies, and error rates.
    """

    def __init__(self, memory: IMemory):
        """Initialize monitoring decorator.

        Args:
            memory: The memory instance to wrap
        """
        super().__init__(memory)
        self._metrics = {
            "operations": {
                "store": {"count": 0, "errors": 0, "total_time": 0.0},
                "load": {"count": 0, "errors": 0, "total_time": 0.0},
                "delete": {"count": 0, "errors": 0, "total_time": 0.0},
                "exists": {"count": 0, "errors": 0, "total_time": 0.0},
                "keys": {"count": 0, "errors": 0, "total_time": 0.0},
                "clear": {"count": 0, "errors": 0, "total_time": 0.0},
                "size": {"count": 0, "errors": 0, "total_time": 0.0},
            },
            "cache_stats": {"hits": 0, "misses": 0, "hit_rate": 0.0},
            "errors": [],
            "slow_operations": [],
        }
        self._lock = asyncio.Lock()
        self.slow_threshold = 1.0  # Operations slower than 1 second

    async def _record_operation(
        self, operation: str, duration: float, error: Optional[Exception] = None
    ) -> None:
        """Record metrics for an operation."""
        async with self._lock:
            stats = self._metrics["operations"][operation]
            stats["count"] += 1
            stats["total_time"] += duration

            if error:
                stats["errors"] += 1
                self._metrics["errors"].append(
                    {
                        "operation": operation,
                        "error": str(error),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if duration > self.slow_threshold:
                self._metrics["slow_operations"].append(
                    {
                        "operation": operation,
                        "duration": duration,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    async def store(self, key: str, value: Any, user_id: Optional[str] = None) -> None:
        """Store a value with monitoring."""
        start_time = time.time()
        error = None

        try:
            await self._memory.store(key, value, user_id)
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("store", duration, error)

    async def load(
        self, key: str, default: Any = None, user_id: Optional[str] = None
    ) -> Any:
        """Load a value with monitoring."""
        start_time = time.time()
        error = None

        try:
            value = await self._memory.load(key, default, user_id)

            # Track cache hits/misses
            async with self._lock:
                if value is not default:
                    self._metrics["cache_stats"]["hits"] += 1
                else:
                    self._metrics["cache_stats"]["misses"] += 1

                total = (
                    self._metrics["cache_stats"]["hits"]
                    + self._metrics["cache_stats"]["misses"]
                )
                if total > 0:
                    self._metrics["cache_stats"]["hit_rate"] = (
                        self._metrics["cache_stats"]["hits"] / total
                    )

            return value
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("load", duration, error)

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete a key with monitoring."""
        start_time = time.time()
        error = None

        try:
            return await self._memory.delete(key, user_id)
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("delete", duration, error)

    async def exists(self, key: str, user_id: Optional[str] = None) -> bool:
        """Check if key exists with monitoring."""
        start_time = time.time()
        error = None

        try:
            return await self._memory.exists(key, user_id)
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("exists", duration, error)

    async def keys(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[str]:
        """Get keys with monitoring."""
        start_time = time.time()
        error = None

        try:
            return await self._memory.keys(pattern, user_id)
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("keys", duration, error)

    async def clear(
        self, pattern: Optional[str] = None, user_id: Optional[str] = None
    ) -> int:
        """Clear keys with monitoring."""
        start_time = time.time()
        error = None

        try:
            return await self._memory.clear(pattern, user_id)
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("clear", duration, error)

    async def size(self, user_id: Optional[str] = None) -> int:
        """Get size with monitoring."""
        start_time = time.time()
        error = None

        try:
            return await self._memory.size(user_id)
        except Exception as e:
            error = e
            raise
        finally:
            duration = time.time() - start_time
            await self._record_operation("size", duration, error)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self._metrics.copy()

    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get stats for a specific operation."""
        stats = self._metrics["operations"].get(operation, {})
        if stats and stats["count"] > 0:
            return {
                **stats,
                "avg_time": stats["total_time"] / stats["count"],
                "error_rate": stats["errors"] / stats["count"],
            }
        return stats
