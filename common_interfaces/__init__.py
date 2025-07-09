from importlib import import_module
from typing import Any, Type

from . import plugins
from .base_plugin import BasePlugin
from .resources import BaseResource

__all__ = [
    "plugins",
    "BasePlugin",
    "BaseResource",
    "import_plugin_class",
]


def import_plugin_class(path: str) -> Type[Any]:
    """Import a class using ``module:Class`` or ``module.Class`` notation."""
    if ":" in path:
        module_path, class_name = path.split(":", 1)
    elif "." in path:
        module_path, class_name = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid plugin path: {path}")
    module = import_module(module_path)
    return getattr(module, class_name)
