"""Public resource wrappers for pipeline consumers."""


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
    raise AttributeError(f"module {__name__} has no attribute {name}")


from .container import ResourceContainer
from .database import DatabaseResource
from .duckdb_database import DuckDBDatabaseResource
from .filesystem import FileSystemResource
from .in_memory_storage import InMemoryStorageResource
from .llm.unified import UnifiedLLMResource
from .memory import Memory
from .memory_resource import MemoryResource, SimpleMemoryResource
from .pg_vector_store import PgVectorStore
from .postgres import PostgresResource
from .sqlite_storage import SQLiteStorageResource
from .storage_resource import StorageResource

__all__ = [
    "MemoryResource",
    "SimpleMemoryResource",
    "UnifiedLLMResource",
    "DatabaseResource",
    "DuckDBDatabaseResource",
    "FileSystemResource",
    "InMemoryStorageResource",
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
