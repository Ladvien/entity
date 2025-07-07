from __future__ import annotations

from dataclasses import MISSING, asdict, dataclass, field, is_dataclass
from typing import Any, Dict, get_args, get_origin, get_type_hints

from jsonschema import validate


@dataclass
class PluginConfig:
    """Configuration for a single plugin."""

    type: str
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginsSection:
    """Collection of user-defined plugins."""

    resources: Dict[str, PluginConfig] = field(default_factory=dict)
    tools: Dict[str, PluginConfig] = field(default_factory=dict)
    adapters: Dict[str, PluginConfig] = field(default_factory=dict)
    prompts: Dict[str, PluginConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginsSection":
        def _load(section: str) -> Dict[str, PluginConfig]:
            result = {}
            for name, conf in data.get(section, {}).items():
                conf = dict(conf)
                result[name] = PluginConfig(conf.pop("type"), conf)
            return result

        return cls(
            resources=_load("resources"),
            tools=_load("tools"),
            adapters=_load("adapters"),
            prompts=_load("prompts"),
        )


@dataclass
class ServerConfig:
    host: str
    port: int
    reload: bool = False
    log_level: str = "info"


@dataclass
class ToolRegistryConfig:
    """Options controlling tool execution."""

    concurrency_limit: int = 5
    cache_ttl: int | None = None


@dataclass
class EntityConfig:
    server: ServerConfig
    plugins: PluginsSection = field(default_factory=PluginsSection)
    tool_registry: ToolRegistryConfig = field(default_factory=ToolRegistryConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityConfig":
        server = ServerConfig(**data.get("server", {}))
        plugins = PluginsSection.from_dict(data.get("plugins", {}))
        tool_reg_cfg = ToolRegistryConfig(**data.get("tool_registry", {}))
        return cls(server, plugins, tool_reg_cfg)


# ---------------------------------------------------------------------------
# Schema generation and validation helpers
# ---------------------------------------------------------------------------


def _type_to_schema(tp: Any) -> Dict[str, Any]:
    origin = get_origin(tp)
    if origin is dict:
        args = get_args(tp)
        if args and len(args) == 2 and is_dataclass(args[1]):
            return {
                "type": "object",
                "additionalProperties": _class_to_schema(args[1]),
                "default": {},
            }
        return {"type": "object", "default": {}}
    if is_dataclass(tp):
        return _class_to_schema(tp)
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is bool:
        return {"type": "boolean"}
    return {}


def _class_to_schema(cls: type) -> Dict[str, Any]:
    """Generate a JSON schema for ``cls`` dataclass."""

    schema = {"type": "object", "properties": {}, "additionalProperties": False}
    required = []

    hints = get_type_hints(cls)

    for field_obj in cls.__dataclass_fields__.values():
        field_type = hints.get(field_obj.name, field_obj.type)
        schema["properties"][field_obj.name] = _type_to_schema(field_type)
        if field_obj.default is MISSING and field_obj.default_factory is MISSING:
            required.append(field_obj.name)

    if required:
        schema["required"] = required

    return schema


CONFIG_SCHEMA = _class_to_schema(EntityConfig)


def validate_config(data: Dict[str, Any]) -> None:
    """Validate ``data`` using the generated schema."""

    validate(instance=data, schema=CONFIG_SCHEMA)


__all__ = [
    "PluginConfig",
    "PluginsSection",
    "ServerConfig",
    "ToolRegistryConfig",
    "EntityConfig",
    "CONFIG_SCHEMA",
    "validate_config",
    "asdict",
]
