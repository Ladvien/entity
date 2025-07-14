from __future__ import annotations

"""Pydantic models for Entity configuration."""

from typing import Any, Dict
import os
import socket

from pydantic import BaseModel, Field, validator
from entity.pipeline.stages import PipelineStage
from entity.workflows.base import Workflow


class PluginConfig(BaseModel):
    """Configuration for a single plugin."""

    type: str
    dependencies: list[str] = Field(default_factory=list)
    stage: PipelineStage | None = None
    stages: list[PipelineStage] = Field(default_factory=list)

    class Config:
        extra = "allow"

    @validator("stage", pre=True)
    def _validate_stage(cls, value: str | PipelineStage | None) -> PipelineStage | None:
        if value is None:
            return None
        return PipelineStage.ensure(value)

    @validator("stages", pre=True)
    def _validate_stages(
        cls, value: list[str | PipelineStage] | None
    ) -> list[PipelineStage]:
        if value is None:
            return []
        return [PipelineStage.ensure(v) for v in value]


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


class RateLimitConfig(BaseModel):
    """Request throttling settings for an adapter."""

    requests: int = Field(ge=1, default=1)
    interval: int = Field(ge=1, default=60)


class AdapterSettings(BaseModel):
    """Configuration for adapter plugins."""

    stages: list[str] = Field(default_factory=list)
    auth_tokens: list[str] = Field(default_factory=list)
    rate_limit: RateLimitConfig | None = None
    audit_log_path: str | None = None
    dashboard: bool = False


class WorkflowSettings(BaseModel):
    """Mapping of pipeline stages to plugin names."""

    stages: Dict[str, list[str]] = Field(default_factory=dict)


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
    max_size: int | None = None
    backup_count: int | None = None


class LoggingConfig(BaseModel):
    """Settings controlling the :class:`LoggingResource`."""

    host_name: str = Field(default_factory=socket.gethostname)
    process_id: int = Field(default_factory=os.getpid)
    outputs: list[LogOutputConfig] = Field(default_factory=lambda: [LogOutputConfig()])


class EntityConfig(BaseModel):
    server: ServerConfig = Field(
        default_factory=lambda: ServerConfig(host="localhost", port=8000)
    )
    plugins: PluginsSection = Field(default_factory=PluginsSection)
    workflow: WorkflowSettings | None = Field(default=None)

    @validator("workflow", pre=True)
    def _validate_workflow(
        cls, value: WorkflowSettings | Workflow | Dict[str, Any] | None
    ) -> WorkflowSettings | None:
        if value is None:
            return None
        if isinstance(value, Workflow):
            value = value.to_dict()
        if isinstance(value, dict):
            mapping = value.get("stages", value)
            return WorkflowSettings(
                stages={str(k): list(v) for k, v in mapping.items()}
            )
        return value

    tool_registry: ToolRegistryConfig = Field(default_factory=ToolRegistryConfig)
    runtime_validation_breaker: CircuitBreakerConfig = Field(
        default_factory=CircuitBreakerConfig
    )
    breaker_settings: BreakerSettings = Field(default_factory=BreakerSettings)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityConfig":
        return cls.parse_obj(data)


def asdict(model: BaseModel) -> Dict[str, Any]:
    """Return a dictionary representation of ``model``."""

    return model.dict()


def validate_config(data: Dict[str, Any]) -> None:
    """Validate ``data`` by instantiating :class:`EntityConfig`."""

    EntityConfig.parse_obj(data)


__all__ = [
    "PluginConfig",
    "EmbeddingModelConfig",
    "PluginsSection",
    "ServerConfig",
    "RateLimitConfig",
    "AdapterSettings",
    "ToolRegistryConfig",
    "CircuitBreakerConfig",
    "BreakerSettings",
    "MemoryConfig",
    "LLMConfig",
    "StorageConfig",
    "LogOutputConfig",
    "LoggingConfig",
    "WorkflowSettings",
    "EntityConfig",
    "validate_config",
    "asdict",
]
