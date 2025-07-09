"""Resource implementations shipped with the framework."""

from .base import BaseResource, Resource
from .bedrock import BedrockResource
from entity.core.resources.container import ResourceContainer
from .database import DatabaseResource
from .dsl import ResourceDef, ResourceGraph
from .duckdb_database import DuckDBDatabaseResource
from .duckdb_vector_store import DuckDBVectorStore
from .filesystem import FileSystemResource
from .llm_base import LLM
from .llm_resource import LLMResource
from .postgres import PostgresResource
from .echo_llm import EchoLLMResource
from .local_filesystem import LocalFileSystemResource
from .memory_filesystem import MemoryFileSystem
from .metrics import MetricsResource
from .pg_vector_store import PgVectorStore
from .s3_filesystem import S3FileSystem
from .structured_logging import StructuredLogging
from .vector_store import VectorStore, VectorStoreResource

__all__ = [
    "LLM",
    "DatabaseResource",
    "FileSystemResource",
    "VectorStore",
    "VectorStoreResource",
    "ResourceContainer",
    "Resource",
    "BaseResource",
    "LLMResource",
    "EchoLLMResource",
    "StructuredLogging",
    "MetricsResource",
    "DuckDBDatabaseResource",
    "PgVectorStore",
    "PostgresResource",
    "MemoryFileSystem",
    "DuckDBVectorStore",
    "LocalFileSystemResource",
    "S3FileSystem",
    "BedrockResource",
    "ResourceDef",
    "ResourceGraph",
]
