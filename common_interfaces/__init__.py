from importlib import import_module
from .plugins import plugin_base_registry, configure_plugins
from .base_plugin import BasePlugin


def import_plugin_class(path: str):
    if ":" in path:
        module_path, class_name = path.split(":", 1)
    else:
        module_path, class_name = path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


__all__ = [
    "plugin_base_registry",
    "configure_plugins",
    "BasePlugin",
    "import_plugin_class",
]
