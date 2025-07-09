from types import SimpleNamespace

from pipeline.base_plugins.resource import ResourcePlugin as BaseResource
from pipeline.base_plugins.base import BasePlugin

plugin_base_registry = SimpleNamespace(auto_plugin=object)


def configure_plugins(*args, **kwargs):
    pass


__all__ = ["plugin_base_registry", "configure_plugins", "BaseResource", "BasePlugin"]
