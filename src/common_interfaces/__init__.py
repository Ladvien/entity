"""Compatibility shims for the Entity codebase."""

from . import plugins
from .base_plugin import BasePlugin
from .plugins import import_plugin_class
from .resources import BaseResource

__all__ = [
    "plugins",
    "BasePlugin",
    "BaseResource",
    "import_plugin_class",
]
