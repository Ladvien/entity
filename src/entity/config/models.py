from __future__ import annotations

"""Pydantic models for Entity configuration."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class PluginConfig(BaseModel):
    """Configuration for a single plugin."""

    type: str

    class Config:
        extra = "allow"


class EmbeddingModelConfig(BaseModel):
    name: str
    dimensions: int | None = None

    class Config:
        extra = "allow"


class PluginsSection(BaseModel):
    """Collection of user-defined plugins grouped by category."""

    infrastructure: Dict[str, PluginConfig] = Field(default_factory=dict)
    resources: Dict[str, PluginConfig] = Field(default_factory=dict)
    agent_resources: Dict[str, PluginConfig] = Field(default_factory=dict)
    custom_resources: Dict[str, PluginConfig] = Field(default_factory=dict)
    tools: Dict[str, PluginConfig] = Field(default_factory=dict)
    adapters: Dict[str, PluginConfig] = Field(default_factory=dict)
    prompts: Dict[str, PluginConfig] = Field(default_factory=dict)


class ServerConfig(BaseModel):
    host: str
    port: int
    reload: bool = False
    log_level: str = "info"


class ToolRegistryConfig(BaseModel):
    """Options controlling tool execution."""

    concurrency_limit: int = 5


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    failure_threshold: int = 3
    recovery_timeout: float = 60.0
    database: int | None = 3
    api: int | None = 5
    filesystem: int | None = 2

    class Config:
        extra = "allow"


class BreakerSettings(BaseModel):
    """Circuit breaker settings for different resource types."""

    database: CircuitBreakerConfig = Field(
        default_factory=lambda: CircuitBreakerConfig(failure_threshold=3)
    )
    external_api: CircuitBreakerConfig = Field(
        default_factory=lambda: CircuitBreakerConfig(failure_threshold=5)
    )
    file_system: CircuitBreakerConfig = Field(
        default_factory=lambda: CircuitBreakerConfig(failure_threshold=2)
    )


class MemoryConfig(BaseModel):
    """Configuration model for the :class:`~entity.resources.memory.Memory`."""

    kv_table: str = "memory_kv"
    history_table: str = "conversation_history"

    class Config:
        extra = "forbid"


class LLMConfig(BaseModel):
    """Configuration model for the :class:`~entity.resources.llm.LLM`."""

    provider: str = "default"

    class Config:
        extra = "forbid"


class StorageConfig(BaseModel):
    """Configuration model for the :class:`~entity.resources.storage.Storage`."""

    namespace: str = "default"

    class Config:
        extra = "forbid"


class LogOutputConfig(BaseModel):
    """Configuration for a single logging output."""

    type: str = "console"
    level: str = "info"
    path: str | None = None
    host: str | None = None
    port: int | None = None


class LoggingConfig(BaseModel):
    """Settings controlling the :class:`LoggingResource`."""

    outputs: list[LogOutputConfig] = Field(default_factory=lambda: [LogOutputConfig()])


class EntityConfig(BaseModel):
    server: ServerConfig = Field(
        default_factory=lambda: ServerConfig(host="localhost", port=8000)
    )
    plugins: PluginsSection = Field(default_factory=PluginsSection)
    workflow: Dict[str, list[str]] | None = Field(default=None)
    tool_registry: ToolRegistryConfig = Field(default_factory=ToolRegistryConfig)
    runtime_validation_breaker: CircuitBreakerConfig = Field(
        default_factory=CircuitBreakerConfig
    )
    breaker_settings: BreakerSettings = Field(default_factory=BreakerSettings)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityConfig":
        return cls.model_validate(data)


def asdict(model: BaseModel) -> Dict[str, Any]:
    """Return a dictionary representation of ``model``."""

    return model.model_dump()


def validate_config(data: Dict[str, Any]) -> None:
    """Validate ``data`` by instantiating :class:`EntityConfig`."""

    EntityConfig.model_validate(data)


__all__ = [
    "PluginConfig",
    "EmbeddingModelConfig",
    "PluginsSection",
    "ServerConfig",
    "ToolRegistryConfig",
    "CircuitBreakerConfig",
    "BreakerSettings",
    "MemoryConfig",
    "LLMConfig",
    "StorageConfig",
    "LogOutputConfig",
    "LoggingConfig",
    "EntityConfig",
    "validate_config",
    "asdict",
]
