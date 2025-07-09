from __future__ import annotations

"""Pydantic models for Entity configuration."""

from typing import Any, Dict

from pydantic import BaseModel, Field, model_validator


class PluginConfig(BaseModel):
    """Configuration for a single plugin."""

    type: str

    class Config:
        extra = "allow"


class BackendConfig(BaseModel):
    """Generic backend configuration."""

    type: str

    class Config:
        extra = "allow"


class MemoryConfig(PluginConfig):
    database: BackendConfig | None = None
    vector_store: PluginConfig | None = None


class EmbeddingModelConfig(BaseModel):
    name: str
    dimensions: int | None = None

    class Config:
        extra = "allow"


class VectorMemoryConfig(PluginConfig):
    table: str
    embedding_model: EmbeddingModelConfig


class PluginsSection(BaseModel):
    """Collection of user-defined plugins grouped by category."""

    resources: Dict[str, PluginConfig] = Field(default_factory=dict)
    tools: Dict[str, PluginConfig] = Field(default_factory=dict)
    adapters: Dict[str, PluginConfig] = Field(default_factory=dict)
    prompts: Dict[str, PluginConfig] = Field(default_factory=dict)

    @model_validator(mode="before")
    def _specialize_resources(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        resources = values.get("resources", {}) or {}
        if "memory" in resources:
            resources["memory"] = MemoryConfig.model_validate(resources["memory"])
        if "vector_store" in resources:
            resources["vector_store"] = VectorMemoryConfig.model_validate(
                resources["vector_store"]
            )
        values["resources"] = resources
        return values


class ServerConfig(BaseModel):
    host: str
    port: int
    reload: bool = False
    log_level: str = "info"


class ToolRegistryConfig(BaseModel):
    """Options controlling tool execution."""

    concurrency_limit: int = 5
    cache_ttl: int | None = None


class EntityConfig(BaseModel):
    server: ServerConfig = Field(
        default_factory=lambda: ServerConfig(host="localhost", port=8000)
    )
    plugins: PluginsSection = Field(default_factory=PluginsSection)
    workflow: Dict[str, list[str]] | None = Field(default=None)
    tool_registry: ToolRegistryConfig = Field(default_factory=ToolRegistryConfig)

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
    "BackendConfig",
    "MemoryConfig",
    "EmbeddingModelConfig",
    "VectorMemoryConfig",
    "PluginsSection",
    "ServerConfig",
    "ToolRegistryConfig",
    "EntityConfig",
    "validate_config",
    "asdict",
]
