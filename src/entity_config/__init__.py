"""Configuration helpers for Entity."""

# flake8: noqa
import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from .builder import ConfigBuilder
from .models import (
    CONFIG_SCHEMA,
    EntityConfig,
    PluginConfig,
    BackendConfig,
    MemoryConfig,
    CacheConfig,
    EmbeddingModelConfig,
    VectorMemoryConfig,
    PluginsSection,
    ServerConfig,
    ToolRegistryConfig,
    validate_config,
)

__all__ = [
    "ConfigBuilder",
    "PluginConfig",
    "BackendConfig",
    "MemoryConfig",
    "CacheConfig",
    "EmbeddingModelConfig",
    "VectorMemoryConfig",
    "PluginsSection",
    "ServerConfig",
    "ToolRegistryConfig",
    "EntityConfig",
    "CONFIG_SCHEMA",
    "validate_config",
]
