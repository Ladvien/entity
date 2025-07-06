from pydantic import BaseModel


class DefaultConfigModel(BaseModel):
    class Config:
        extra = "allow"


__all__ = ["DefaultConfigModel"]


# Adapter configs
class CLIAdapterConfig(DefaultConfigModel):
    pass


class LLMGRPCAdapterConfig(DefaultConfigModel):
    host: str | None = None
    port: int | None = None


class HTTPAdapterConfig(DefaultConfigModel):
    host: str | None = None
    port: int | None = None
    dashboard: bool | None = None


class LoggingAdapterConfig(DefaultConfigModel):
    pass


class WebSocketAdapterConfig(DefaultConfigModel):
    host: str | None = None
    port: int | None = None


# Prompt configs
class MemoryPluginConfig(DefaultConfigModel):
    pass


class ComplexPromptConfig(DefaultConfigModel):
    k: int | None = None


class ConversationHistoryConfig(DefaultConfigModel):
    pass


class MemoryRetrievalPromptConfig(DefaultConfigModel):
    pass


class ChatHistoryConfig(DefaultConfigModel):
    pass


# Tool configs
class WeatherApiToolConfig(DefaultConfigModel):
    base_url: str | None = None
    api_key: str | None = None
    timeout: int | None = None


class CalculatorToolConfig(DefaultConfigModel):
    pass


class SearchToolConfig(DefaultConfigModel):
    pass


# Resource configs
class BedrockResourceConfig(DefaultConfigModel):
    region: str | None = None
    model_id: str | None = None


class ClaudeResourceConfig(DefaultConfigModel):
    pass


class DuckDBDatabaseResourceConfig(DefaultConfigModel):
    path: str | None = None
    history_table: str | None = None


class DuckDBVectorStoreConfig(DefaultConfigModel):
    path: str | None = None


class EchoLLMResourceConfig(DefaultConfigModel):
    pass


class GeminiResourceConfig(DefaultConfigModel):
    pass


class InMemoryStorageResourceConfig(DefaultConfigModel):
    history_table: str | None = None


class LocalFileSystemResourceConfig(DefaultConfigModel):
    base_path: str | None = None


class OllamaLLMResourceConfig(DefaultConfigModel):
    pass


class OpenAIResourceConfig(DefaultConfigModel):
    pass


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
    "MemoryPluginConfig",
    "ComplexPromptConfig",
    "ConversationHistoryConfig",
    "MemoryRetrievalPromptConfig",
    "ChatHistoryConfig",
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
    "CLIAdapter": CLIAdapterConfig,
    "LLMGRPCAdapter": LLMGRPCAdapterConfig,
    "HTTPAdapter": HTTPAdapterConfig,
    "LoggingAdapter": LoggingAdapterConfig,
    "WebSocketAdapter": WebSocketAdapterConfig,
    "MemoryPlugin": MemoryPluginConfig,
    "ComplexPrompt": ComplexPromptConfig,
    "ConversationHistory": ConversationHistoryConfig,
    "MemoryRetrievalPrompt": MemoryRetrievalPromptConfig,
    "ChatHistory": ChatHistoryConfig,
    "WeatherApiTool": WeatherApiToolConfig,
    "CalculatorTool": CalculatorToolConfig,
    "SearchTool": SearchToolConfig,
    "BedrockResource": BedrockResourceConfig,
    "ClaudeResource": ClaudeResourceConfig,
    "DuckDBDatabaseResource": DuckDBDatabaseResourceConfig,
    "DuckDBVectorStore": DuckDBVectorStoreConfig,
    "EchoLLMResource": EchoLLMResourceConfig,
    "GeminiResource": GeminiResourceConfig,
    "InMemoryStorageResource": InMemoryStorageResourceConfig,
    "LocalFileSystemResource": LocalFileSystemResourceConfig,
    "OllamaLLMResource": OllamaLLMResourceConfig,
    "OpenAIResource": OpenAIResourceConfig,
    "PgVectorStore": PgVectorStoreConfig,
    "PostgresResource": PostgresResourceConfig,
    "SQLiteStorageResource": SQLiteStorageResourceConfig,
    "StorageResource": StorageResourceConfig,
    "StructuredLogging": StructuredLoggingConfig,
    "S3FileSystem": S3FileSystemConfig,
}
