"""Registry utilities and data structures."""

from __future__ import annotations

from .registries import PluginRegistry, SystemRegistries, ToolRegistry
from .validator import RegistryValidator

__all__ = [
    "PluginRegistry",
    "ToolRegistry",
    "SystemRegistries",
    "RegistryValidator",
]


def __getattr__(name: str):
    """Lazily load pipeline dependencies."""

    if name == "ResourceContainer":
        from pipeline.resources import ResourceContainer

        return ResourceContainer
    raise AttributeError(f"module {__name__} has no attribute {name}")
