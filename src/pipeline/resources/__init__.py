"""Public resource wrappers for pipeline consumers."""

# Lazy imports so optional resources don't load heavy dependencies.

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.base import BaseResource, Resource
    from plugins.builtin.resources.llm_base import LLM
    from plugins.builtin.resources.llm_resource import LLMResource

    from entity.core.resources.container import ResourceContainer
    from .database import DatabaseResource
    from .duckdb_database import DuckDBDatabaseResource
    from .filesystem import FileSystemResource
    from .in_memory_storage import InMemoryStorageResource
    from .llm.unified import UnifiedLLMResource
    from .memory import Memory
    from .memory_filesystem import MemoryFileSystem
    from .memory_storage import MemoryStorage
    from .memory_vector_store import MemoryVectorStore
    from .pg_vector_store import PgVectorStore
    from .postgres import PostgresResource
    from .sqlite_storage import SQLiteStorageResource
    from .storage_resource import StorageResource


def __getattr__(name: str):
    if name in {"BaseResource", "Resource"}:
        from plugins.builtin.resources.base import BaseResource, Resource

        return {"BaseResource": BaseResource, "Resource": Resource}[name]
    if name == "LLM":
        from plugins.builtin.resources.llm_base import LLM

        return LLM
    if name == "LLMResource":
        from plugins.builtin.resources.llm_resource import LLMResource

        return LLMResource
    if name == "ResourceContainer":
        from entity.core.resources.container import ResourceContainer

        return ResourceContainer
    if name == "DatabaseResource":
        from .database import DatabaseResource

        return DatabaseResource
    if name == "DuckDBDatabaseResource":
        from .duckdb_database import DuckDBDatabaseResource

        return DuckDBDatabaseResource
    if name == "FileSystemResource":
        from .filesystem import FileSystemResource

        return FileSystemResource
    if name == "InMemoryStorageResource":
        from .in_memory_storage import InMemoryStorageResource

        return InMemoryStorageResource
    if name == "UnifiedLLMResource":
        from .llm.unified import UnifiedLLMResource

        return UnifiedLLMResource
    if name == "Memory":
        from .memory import Memory

        return Memory
    if name == "MemoryFileSystem":
        from .memory_filesystem import MemoryFileSystem

        return MemoryFileSystem
    if name == "MemoryStorage":
        from .memory_storage import MemoryStorage

        return MemoryStorage
    if name == "MemoryVectorStore":
        from .memory_vector_store import MemoryVectorStore

        return MemoryVectorStore
    if name == "PgVectorStore":
        from .pg_vector_store import PgVectorStore

        return PgVectorStore
    if name == "PostgresResource":
        from .postgres import PostgresResource

        return PostgresResource
    if name == "SQLiteStorageResource":
        from .sqlite_storage import SQLiteStorageResource

        return SQLiteStorageResource
    if name == "StorageResource":
        from .storage_resource import StorageResource

        return StorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "UnifiedLLMResource",
    "DatabaseResource",
    "DuckDBDatabaseResource",
    "FileSystemResource",
    "InMemoryStorageResource",
    "MemoryStorage",
    "MemoryVectorStore",
    "MemoryFileSystem",
    "Memory",
    "PgVectorStore",
    "PostgresResource",
    "SQLiteStorageResource",
    "StorageResource",
    "ResourceContainer",
    "LLM",
    "LLMResource",
    "Resource",
    "BaseResource",
]
