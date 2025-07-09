from __future__ import annotations

"""Compatibility layer exposing plugin utilities."""

from entity.core.plugin_utils import (
    PluginAutoClassifier,
    configure_plugins,
    import_plugin_class,
)

__all__ = [
    "PluginAutoClassifier",
    "import_plugin_class",
    "configure_plugins",
]
