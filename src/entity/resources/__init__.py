"""Public resource interfaces and canonical wrappers."""

from entity.resources.argument_parsing import (
    ArgumentCategory,
    ArgumentDefinition,
    ArgumentParsingResource,
    ArgumentType,
    CommandDefinition,
    EntityArgumentParsingResource,
    create_argument_parsing_resource,
)
from entity.resources.database import DatabaseResource
from entity.resources.exceptions import ResourceInitializationError
from entity.resources.file_storage_wrapper import FileStorage
from entity.resources.llm import LLMResource
from entity.resources.llm_wrapper import LLM
from entity.resources.local_storage import LocalStorageResource
from entity.resources.logging import (
    LogLevel,
    RichConsoleLoggingResource,
    RichJSONLoggingResource,
    RichLoggingResource,
)
from entity.resources.memory import Memory
from entity.resources.metrics import MetricsCollectorResource
from entity.resources.storage import StorageResource
from entity.resources.vector_store import VectorStoreResource

from .exceptions import InfrastructureError

__all__ = [
    "DatabaseResource",
    "VectorStoreResource",
    "LLMResource",
    "StorageResource",
    "LocalStorageResource",
    "ResourceInitializationError",
    "Memory",
    "LLM",
    "FileStorage",
    "RichLoggingResource",
    "RichConsoleLoggingResource",
    "RichJSONLoggingResource",
    "LogLevel",
    "MetricsCollectorResource",
    "ArgumentParsingResource",
    "EntityArgumentParsingResource",
    "ArgumentDefinition",
    "CommandDefinition",
    "ArgumentType",
    "ArgumentCategory",
    "create_argument_parsing_resource",
    "InfrastructureError",
]
