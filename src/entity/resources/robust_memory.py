"""Robust Cross-Process Memory with Advanced Locking Mechanisms.

This module implements Story 12 - Robust Cross-Process Locking, replacing
the basic file-based locking with a comprehensive system using portalocker
for timeout-based lock acquisition, orphaned lock cleanup, and monitoring.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

import portalocker

from .memory import Memory


class LockTimeoutError(Exception):
    """Raised when lock acquisition times out."""

    def __init__(self, timeout: float, lock_path: str):
        self.timeout = timeout
        self.lock_path = lock_path
        super().__init__(f"Failed to acquire lock {lock_path} within {timeout} seconds")


class LockMonitor:
    """Monitor and metrics collector for lock operations."""

    def __init__(self):
        self.lock_acquisitions = 0
        self.lock_failures = 0
        self.lock_timeouts = 0
        self.orphaned_locks_cleaned = 0
        self.total_lock_time = 0.0
        self.max_wait_time = 0.0

    def record_acquisition(self, wait_time: float):
        """Record successful lock acquisition."""
        self.lock_acquisitions += 1
        self.total_lock_time += wait_time
        self.max_wait_time = max(self.max_wait_time, wait_time)

    def record_failure(self):
        """Record lock acquisition failure."""
        self.lock_failures += 1

    def record_timeout(self):
        """Record lock acquisition timeout."""
        self.lock_timeouts += 1

    def record_orphaned_cleanup(self):
        """Record orphaned lock cleanup."""
        self.orphaned_locks_cleaned += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get current lock metrics."""
        avg_wait_time = (
            self.total_lock_time / self.lock_acquisitions
            if self.lock_acquisitions > 0
            else 0.0
        )

        return {
            "acquisitions": self.lock_acquisitions,
            "failures": self.lock_failures,
            "timeouts": self.lock_timeouts,
            "orphaned_cleaned": self.orphaned_locks_cleaned,
            "avg_wait_time": avg_wait_time,
            "max_wait_time": self.max_wait_time,
            "success_rate": (
                self.lock_acquisitions / (self.lock_acquisitions + self.lock_failures)
                if (self.lock_acquisitions + self.lock_failures) > 0
                else 1.0
            ),
        }


class RobustInterProcessLock:
    """Robust cross-process lock with timeout and cleanup capabilities."""

    def __init__(
        self, path: str, timeout: float = 5.0, monitor: Optional[LockMonitor] = None
    ):
        self.path = Path(path)
        self.timeout = timeout
        self.monitor = monitor or LockMonitor()
        self.logger = logging.getLogger(__name__)
        self._file = None
        self._start_time = None

        # Create lock directory if it doesn't exist
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self) -> "RobustInterProcessLock":
        """Acquire lock with timeout and monitoring."""
        return await self.acquire()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Release lock and record metrics."""
        await self.release()

    async def acquire(self) -> "RobustInterProcessLock":
        """Acquire the lock with timeout and cleanup handling."""
        self._start_time = time.time()

        try:
            # Check for and clean orphaned locks
            await self._cleanup_orphaned_locks()

            # Attempt to acquire lock with timeout
            await self._acquire_with_timeout()

            wait_time = time.time() - self._start_time
            self.monitor.record_acquisition(wait_time)

            self.logger.debug(f"Acquired lock {self.path} after {wait_time:.3f}s")
            return self

        except Exception as e:
            if isinstance(e, LockTimeoutError):
                self.monitor.record_timeout()
            else:
                self.monitor.record_failure()
            self.logger.warning(f"Failed to acquire lock {self.path}: {e}")
            raise

    async def _acquire_with_timeout(self) -> None:
        """Acquire lock with timeout using portalocker."""
        try:
            # Open file for locking
            self._file = await asyncio.to_thread(open, self.path, "w")

            # Write process info for orphan detection
            process_info = {
                "pid": os.getpid(),
                "timestamp": time.time(),
                "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
            }

            await asyncio.to_thread(
                self._file.write,
                f"{process_info['pid']}\n{process_info['timestamp']}\n{process_info['host']}\n",
            )
            await asyncio.to_thread(self._file.flush)

            # Attempt to acquire lock with timeout
            end_time = time.time() + self.timeout

            while time.time() < end_time:
                try:
                    await asyncio.to_thread(
                        portalocker.lock,
                        self._file,
                        portalocker.LOCK_EX | portalocker.LOCK_NB,
                    )
                    return  # Successfully acquired lock
                except portalocker.LockException:
                    # Lock is held by another process, wait and retry
                    await asyncio.sleep(0.01)  # 10ms retry interval

            # Timeout exceeded
            self._file.close()
            self._file = None
            raise LockTimeoutError(self.timeout, str(self.path))

        except Exception as e:
            if self._file:
                self._file.close()
                self._file = None
            if not isinstance(e, LockTimeoutError):
                raise LockTimeoutError(self.timeout, str(self.path)) from e
            raise

    async def release(self) -> None:
        """Release the lock and clean up."""
        if self._file:
            try:
                await asyncio.to_thread(portalocker.unlock, self._file)
                self._file.close()

                # Remove lock file to prevent accumulation
                try:
                    self.path.unlink(missing_ok=True)
                except OSError:
                    pass  # File might have been removed by another process

                wait_time = time.time() - (self._start_time or time.time())
                self.logger.debug(f"Released lock {self.path} after {wait_time:.3f}s")

            except Exception as e:
                self.logger.warning(f"Error releasing lock {self.path}: {e}")
            finally:
                self._file = None

    async def _cleanup_orphaned_locks(self) -> None:
        """Clean up orphaned locks from dead processes."""
        if not self.path.exists():
            return

        try:
            # Read lock file to get process info
            content = await asyncio.to_thread(self.path.read_text)
            lines = content.strip().split("\n")

            if len(lines) >= 2:
                try:
                    pid = int(lines[0])
                    timestamp = float(lines[1])

                    # Check if process is still alive
                    if not self._is_process_alive(pid):
                        # Process is dead, clean up orphaned lock
                        self.path.unlink(missing_ok=True)
                        self.monitor.record_orphaned_cleanup()
                        self.logger.info(
                            f"Cleaned up orphaned lock from dead process {pid}"
                        )

                    elif time.time() - timestamp > 3600:  # 1 hour timeout
                        # Lock is very old, likely orphaned
                        self.path.unlink(missing_ok=True)
                        self.monitor.record_orphaned_cleanup()
                        self.logger.info(
                            f"Cleaned up stale lock (>1 hour old) from process {pid}"
                        )

                except (ValueError, OSError) as e:
                    # Corrupted lock file, remove it
                    self.path.unlink(missing_ok=True)
                    self.monitor.record_orphaned_cleanup()
                    self.logger.info(f"Cleaned up corrupted lock file: {e}")

        except Exception as e:
            self.logger.warning(f"Error during orphaned lock cleanup: {e}")

    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process is still alive."""
        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except OSError:
            return False
        except ProcessLookupError:
            return False


class RobustMemory(Memory):
    """Enhanced Memory class with robust cross-process locking.

    This class implements Story 12 acceptance criteria:
    - Timeout-based lock acquisition
    - Automatic lock cleanup on process termination
    - Lock recovery mechanism for orphaned locks
    - Lock monitoring and metrics
    - Comprehensive lock timeout configuration
    """

    def __init__(
        self,
        database,
        vector_store,
        lock_timeout: float = 5.0,
        cleanup_orphaned: bool = True,
        monitor_locks: bool = True,
    ):
        """Initialize RobustMemory with enhanced locking.

        Args:
            database: Database resource for structured data storage.
            vector_store: Vector store resource for semantic search.
            lock_timeout: Timeout for lock acquisition in seconds.
            cleanup_orphaned: Whether to automatically cleanup orphaned locks.
            monitor_locks: Whether to collect lock metrics.
        """
        # Call parent constructor but override locking mechanism
        super().__init__(database, vector_store)

        self.lock_timeout = lock_timeout
        self.cleanup_orphaned = cleanup_orphaned
        self.monitor = LockMonitor() if monitor_locks else None

        # Replace the simple _InterProcessLock with RobustInterProcessLock
        db_path = getattr(self.database.infrastructure, "file_path", None)
        if db_path is not None:
            lock_file = Path(str(db_path)).with_suffix(".lock")
            self._process_lock = RobustInterProcessLock(
                str(lock_file), timeout=self.lock_timeout, monitor=self.monitor
            )
        else:
            self._process_lock = None

        # Register cleanup handler for graceful shutdown
        self._register_cleanup_handlers()

        self.logger = logging.getLogger(__name__)

    def _register_cleanup_handlers(self):
        """Register signal handlers for graceful lock cleanup."""

        def cleanup_handler(signum, frame):
            """Handle process termination signals."""
            if self._process_lock and self._process_lock._file:
                try:
                    # Synchronous cleanup for signal handlers
                    portalocker.unlock(self._process_lock._file)
                    self._process_lock._file.close()
                    self._process_lock.path.unlink(missing_ok=True)
                except Exception:
                    pass  # Best effort cleanup

        # Register for common termination signals
        for sig in [signal.SIGTERM, signal.SIGINT]:
            try:
                signal.signal(sig, cleanup_handler)
            except (OSError, ValueError):
                # Some signals might not be available on all platforms
                pass

    @asynccontextmanager
    async def _acquire_lock(
        self, timeout: Optional[float] = None
    ) -> AsyncGenerator[None, None]:
        """Acquire robust cross-process lock with optional timeout override."""
        if self._process_lock is None:
            yield
            return

        # Use provided timeout or default
        original_timeout = self._process_lock.timeout
        if timeout is not None:
            self._process_lock.timeout = timeout

        try:
            async with self._process_lock:
                yield
        finally:
            # Restore original timeout
            self._process_lock.timeout = original_timeout

    async def _execute_with_locks(
        self,
        query: str,
        *params: Any,
        fetch_one: bool = False,
        lock_timeout: Optional[float] = None,
    ) -> Any:
        """Execute a database query with robust locking."""
        if self._process_lock is not None:
            async with self._acquire_lock(timeout=lock_timeout):
                await self._ensure_table()
                async with self._lock:
                    result = await asyncio.to_thread(
                        self.database.execute,
                        query,
                        *params,
                    )
                    if fetch_one:
                        return result.fetchone() if result else None
                    return result
        else:
            async with self._lock:
                await self._ensure_table()
                result = await asyncio.to_thread(
                    self.database.execute,
                    query,
                    *params,
                )
                if fetch_one:
                    return result.fetchone() if result else None
                return result

    def get_lock_metrics(self) -> dict[str, Any]:
        """Get current lock performance metrics."""
        if self.monitor:
            return self.monitor.get_metrics()
        return {}

    async def cleanup_orphaned_locks(self) -> int:
        """Manually trigger orphaned lock cleanup.

        Returns:
            Number of orphaned locks cleaned up.
        """
        if not self._process_lock or not self.cleanup_orphaned:
            return 0

        initial_count = self.monitor.orphaned_locks_cleaned if self.monitor else 0
        await self._process_lock._cleanup_orphaned_locks()
        final_count = self.monitor.orphaned_locks_cleaned if self.monitor else 0

        return final_count - initial_count

    def configure_lock_timeout(self, timeout: float) -> None:
        """Configure lock acquisition timeout.

        Args:
            timeout: New timeout value in seconds.
        """
        self.lock_timeout = timeout
        if self._process_lock:
            self._process_lock.timeout = timeout

        self.logger.info(f"Lock timeout configured to {timeout} seconds")
