"""Factory functions for creating memory instances with backward compatibility."""

from __future__ import annotations

import warnings
from typing import Optional

from entity.resources.database import DatabaseResource
from entity.resources.memory_components import BaseMemory, IMemory
from entity.resources.memory_decorators import (
    AsyncDecorator,
    LockingDecorator,
    LRUDecorator,
    MonitoringDecorator,
    TTLDecorator,
)
from entity.resources.vector_store import VectorStoreResource


def create_memory(
    database: DatabaseResource,
    vector_store: VectorStoreResource,
    table_name: str = "entity_memory",
) -> IMemory:
    """Create a basic memory instance.

    This is the replacement for the old Memory class.

    Args:
        database: Database resource for structured storage
        vector_store: Vector store resource for semantic search
        table_name: Name of the database table to use

    Returns:
        Basic memory instance implementing IMemory protocol
    """
    return BaseMemory(database, vector_store, table_name)


def create_async_memory(
    database: DatabaseResource,
    vector_store: VectorStoreResource,
    table_name: str = "entity_memory",
    max_workers: int = 10,
) -> IMemory:
    """Create an async-capable memory instance.

    This is the replacement for the old AsyncMemory class.

    Args:
        database: Database resource for structured storage
        vector_store: Vector store resource for semantic search
        table_name: Name of the database table to use
        max_workers: Maximum number of worker threads for async operations

    Returns:
        Memory instance with async capabilities
    """
    base_memory = BaseMemory(database, vector_store, table_name)
    return AsyncDecorator(base_memory, max_workers)


def create_managed_memory(
    database: DatabaseResource,
    vector_store: VectorStoreResource,
    table_name: str = "entity_memory",
    default_ttl: Optional[int] = 3600,
    max_entries: int = 1000,
    evict_count: int = 100,
    cleanup_interval: int = 60,
) -> IMemory:
    """Create a managed memory instance with TTL and LRU features.

    This is the replacement for the old ManagedMemory class.

    Args:
        database: Database resource for structured storage
        vector_store: Vector store resource for semantic search
        table_name: Name of the database table to use
        default_ttl: Default time-to-live in seconds (None = no expiry)
        max_entries: Maximum number of entries before LRU eviction
        evict_count: Number of entries to evict when max is reached
        cleanup_interval: Interval in seconds between TTL cleanup runs

    Returns:
        Memory instance with TTL and LRU management
    """
    base_memory = BaseMemory(database, vector_store, table_name)

    if default_ttl is not None:
        memory = TTLDecorator(base_memory, default_ttl, cleanup_interval)
    else:
        memory = base_memory

    memory = LRUDecorator(memory, max_entries, evict_count)

    return memory


def create_robust_memory(
    database: DatabaseResource,
    vector_store: VectorStoreResource,
    table_name: str = "entity_memory",
    lock_dir: str = "/tmp/entity_locks",
    timeout: float = 10.0,
    enable_monitoring: bool = True,
) -> IMemory:
    """Create a robust memory instance with locking and monitoring.

    This is the replacement for the old RobustMemory class.

    Args:
        database: Database resource for structured storage
        vector_store: Vector store resource for semantic search
        table_name: Name of the database table to use
        lock_dir: Directory for lock files
        timeout: Lock acquisition timeout in seconds
        enable_monitoring: Whether to enable metrics collection

    Returns:
        Memory instance with process-safe locking and monitoring
    """
    base_memory = BaseMemory(database, vector_store, table_name)

    memory = LockingDecorator(base_memory, lock_dir, timeout)

    if enable_monitoring:
        memory = MonitoringDecorator(memory)

    return memory


def create_full_featured_memory(
    database: DatabaseResource,
    vector_store: VectorStoreResource,
    table_name: str = "entity_memory",
    default_ttl: Optional[int] = None,
    max_entries: int = 10000,
    evict_count: int = 100,
    cleanup_interval: int = 60,
    lock_dir: str = "/tmp/entity_locks",
    lock_timeout: float = 10.0,
    enable_monitoring: bool = True,
    async_workers: int = 10,
) -> IMemory:
    """Create a fully-featured memory instance with all decorators.

    This combines all available features for maximum functionality.

    Args:
        database: Database resource for structured storage
        vector_store: Vector store resource for semantic search
        table_name: Name of the database table to use
        default_ttl: Default time-to-live in seconds (None = no expiry)
        max_entries: Maximum number of entries before LRU eviction
        evict_count: Number of entries to evict when max is reached
        cleanup_interval: Interval in seconds between TTL cleanup runs
        lock_dir: Directory for lock files
        lock_timeout: Lock acquisition timeout in seconds
        enable_monitoring: Whether to enable metrics collection
        async_workers: Maximum number of worker threads for async operations

    Returns:
        Memory instance with all available features
    """
    base_memory = BaseMemory(database, vector_store, table_name)

    memory = base_memory

    if default_ttl is not None:
        memory = TTLDecorator(memory, default_ttl, cleanup_interval)

    memory = LRUDecorator(memory, max_entries, evict_count)

    memory = LockingDecorator(memory, lock_dir, lock_timeout)

    memory = AsyncDecorator(memory, async_workers)

    if enable_monitoring:
        memory = MonitoringDecorator(memory)

    return memory


class Memory:
    """Deprecated: Use create_memory() factory function instead.

    This class is maintained for backward compatibility only.
    """

    def __new__(
        cls,
        database: DatabaseResource,
        vector_store: VectorStoreResource,
        table_name: str = "entity_memory",
    ):
        warnings.warn(
            "Memory class is deprecated. Use create_memory() factory function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return create_memory(database, vector_store, table_name)


class AsyncMemory:
    """Deprecated: Use create_async_memory() factory function instead.

    This class is maintained for backward compatibility only.
    """

    def __new__(
        cls,
        database: DatabaseResource,
        vector_store: VectorStoreResource,
        table_name: str = "entity_memory",
        max_workers: int = 10,
    ):
        warnings.warn(
            "AsyncMemory class is deprecated. Use create_async_memory() factory function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return create_async_memory(database, vector_store, table_name, max_workers)


class ManagedMemory:
    """Deprecated: Use create_managed_memory() factory function instead.

    This class is maintained for backward compatibility only.
    """

    def __new__(
        cls,
        database: DatabaseResource,
        vector_store: VectorStoreResource,
        table_name: str = "entity_memory",
        default_ttl: Optional[int] = 3600,
        max_entries: int = 1000,
        evict_count: int = 100,
        cleanup_interval: int = 60,
    ):
        warnings.warn(
            "ManagedMemory class is deprecated. Use create_managed_memory() factory function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return create_managed_memory(
            database,
            vector_store,
            table_name,
            default_ttl,
            max_entries,
            evict_count,
            cleanup_interval,
        )


class RobustMemory:
    """Deprecated: Use create_robust_memory() factory function instead.

    This class is maintained for backward compatibility only.
    """

    def __new__(
        cls,
        database: DatabaseResource,
        vector_store: VectorStoreResource,
        table_name: str = "entity_memory",
        lock_dir: str = "/tmp/entity_locks",
        timeout: float = 10.0,
        enable_monitoring: bool = True,
    ):
        warnings.warn(
            "RobustMemory class is deprecated. Use create_robust_memory() factory function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return create_robust_memory(
            database, vector_store, table_name, lock_dir, timeout, enable_monitoring
        )
