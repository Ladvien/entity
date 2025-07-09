"""Thin wrappers exposing plugin utilities."""

from entity.core.plugin_utils import (
    PluginAutoClassifier,
    configure_plugins,
    import_plugin_class,
    plugin_base_registry,
)

__all__ = [
    "PluginAutoClassifier",
    "configure_plugins",
    "import_plugin_class",
    "plugin_base_registry",
]
