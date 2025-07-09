from dataclasses import dataclass
from typing import Type


@dataclass
class PluginBaseRegistry:
    base_plugin: Type = object
    prompt_plugin: Type = object
    adapter_plugin: Type = object
    auto_plugin: Type = object


plugin_base_registry = PluginBaseRegistry()


def configure_plugins(
    base_plugin: Type,
    prompt_plugin: Type,
    adapter_plugin: Type,
    auto_plugin: Type,
) -> PluginBaseRegistry:
    plugin_base_registry.base_plugin = base_plugin
    plugin_base_registry.prompt_plugin = prompt_plugin
    plugin_base_registry.adapter_plugin = adapter_plugin
    plugin_base_registry.auto_plugin = auto_plugin
    return plugin_base_registry
