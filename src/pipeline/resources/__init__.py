"""Public resource wrappers for pipeline consumers."""

from plugins.builtin.resources.base import BaseResource, Resource
from plugins.builtin.resources.llm_base import LLM
from plugins.builtin.resources.llm_resource import LLMResource

from .container import ResourceContainer
from .database import DatabaseResource
from .duckdb_database import DuckDBDatabaseResource
from .filesystem import FileSystemResource
from .in_memory_storage import InMemoryStorageResource
from .llm.unified import UnifiedLLMResource
from .memory import Memory
from .memory_filesystem import MemoryFileSystem
from .memory_resource import MemoryResource, SimpleMemoryResource
from .memory_storage import MemoryStorage
from .memory_vector_store import MemoryVectorStore
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
