"""Built-in plugins and resources."""

from pydantic import BaseModel


class DefaultConfigModel(BaseModel):
    class Config:
        extra = "allow"


class SimpleConfigModel(DefaultConfigModel):
    pass


__all__ = ["DefaultConfigModel", "SimpleConfigModel"]


# Adapter configs
CLIAdapterConfig = SimpleConfigModel


class LLMGRPCAdapterConfig(DefaultConfigModel):
    host: str | None = None
    port: int | None = None


class HTTPAdapterConfig(DefaultConfigModel):
    host: str | None = None
    port: int | None = None
    dashboard: bool | None = None


LoggingAdapterConfig = SimpleConfigModel


class WebSocketAdapterConfig(DefaultConfigModel):
    host: str | None = None
    port: int | None = None


# Prompt configs
class ComplexPromptConfig(DefaultConfigModel):
    k: int | None = None


# Tool configs
class WeatherApiToolConfig(DefaultConfigModel):
    base_url: str | None = None
    api_key: str | None = None
    timeout: int | None = None


CalculatorToolConfig = SimpleConfigModel


SearchToolConfig = SimpleConfigModel


# Resource configs
class BedrockResourceConfig(DefaultConfigModel):
    region: str | None = None
    model_id: str | None = None


ClaudeResourceConfig = SimpleConfigModel


class DuckDBDatabaseResourceConfig(DefaultConfigModel):
    path: str | None = None
    history_table: str | None = None


class DuckDBVectorStoreConfig(DefaultConfigModel):
    path: str | None = None


EchoLLMResourceConfig = SimpleConfigModel


GeminiResourceConfig = SimpleConfigModel


class InMemoryStorageResourceConfig(DefaultConfigModel):
    history_table: str | None = None


class LocalFileSystemResourceConfig(DefaultConfigModel):
    base_path: str | None = None


OllamaLLMResourceConfig = SimpleConfigModel


OpenAIResourceConfig = SimpleConfigModel


class PgVectorStoreConfig(DefaultConfigModel):
    table_name: str | None = None


class PostgresResourceConfig(DefaultConfigModel):
    pool_min_size: int | None = None
    pool_max_size: int | None = None
    db_schema: str | None = None
    history_table: str | None = None


class SQLiteStorageResourceConfig(DefaultConfigModel):
    path: str | None = None
    history_table: str | None = None


class StorageResourceConfig(DefaultConfigModel):
    filesystem: dict | None = None


class StructuredLoggingConfig(DefaultConfigModel):
    level: str | None = None
    file_enabled: bool | None = None
    file_path: str | None = None
    max_file_size: int | None = None
    backup_count: int | None = None


class S3FileSystemConfig(DefaultConfigModel):
    bucket: str | None = None
    base_path: str | None = None


__all__ += [
    "CLIAdapterConfig",
    "LLMGRPCAdapterConfig",
    "HTTPAdapterConfig",
    "LoggingAdapterConfig",
    "WebSocketAdapterConfig",
    "ComplexPromptConfig",
    "WeatherApiToolConfig",
    "CalculatorToolConfig",
    "SearchToolConfig",
    "BedrockResourceConfig",
    "ClaudeResourceConfig",
    "DuckDBDatabaseResourceConfig",
    "DuckDBVectorStoreConfig",
    "EchoLLMResourceConfig",
    "GeminiResourceConfig",
    "InMemoryStorageResourceConfig",
    "LocalFileSystemResourceConfig",
    "OllamaLLMResourceConfig",
    "OpenAIResourceConfig",
    "PgVectorStoreConfig",
    "PostgresResourceConfig",
    "SQLiteStorageResourceConfig",
    "StorageResourceConfig",
    "StructuredLoggingConfig",
    "S3FileSystemConfig",
]

# Map plugin class names to config models
PLUGIN_CONFIG_MODELS = {
    "CLIAdapter": SimpleConfigModel,
    "LLMGRPCAdapter": LLMGRPCAdapterConfig,
    "HTTPAdapter": HTTPAdapterConfig,
    "LoggingAdapter": SimpleConfigModel,
    "WebSocketAdapter": WebSocketAdapterConfig,
    "ComplexPrompt": ComplexPromptConfig,
    "WeatherApiTool": WeatherApiToolConfig,
    "CalculatorTool": SimpleConfigModel,
    "SearchTool": SimpleConfigModel,
    "BedrockResource": BedrockResourceConfig,
    "ClaudeResource": SimpleConfigModel,
    "DuckDBDatabaseResource": DuckDBDatabaseResourceConfig,
    "DuckDBVectorStore": DuckDBVectorStoreConfig,
    "EchoLLMResource": SimpleConfigModel,
    "GeminiResource": SimpleConfigModel,
    "InMemoryStorageResource": InMemoryStorageResourceConfig,
    "LocalFileSystemResource": LocalFileSystemResourceConfig,
    "OllamaLLMResource": SimpleConfigModel,
    "OpenAIResource": SimpleConfigModel,
    "PgVectorStore": PgVectorStoreConfig,
    "PostgresResource": PostgresResourceConfig,
    "SQLiteStorageResource": SQLiteStorageResourceConfig,
    "StorageResource": StorageResourceConfig,
    "StructuredLogging": StructuredLoggingConfig,
    "S3FileSystem": S3FileSystemConfig,
}
