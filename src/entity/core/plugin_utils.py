from __future__ import annotations

"""Utilities for plugin classification and discovery."""

import inspect
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, Optional, Type, cast

from .stages import PipelineStage


@dataclass
class PluginBaseRegistry:
    """Container for plugin base classes used by the classifier."""

    base_plugin: Type = object
    prompt_plugin: Type = object
    adapter_plugin: Type = object
    auto_plugin: Type = object
    tool_plugin: Type = object
    failure_plugin: Type = object
    resource_plugin: Type = object


plugin_base_registry = PluginBaseRegistry()


def default_stages_for_class(plugin_class: Type) -> list[PipelineStage]:
    """Return default stages based on plugin class hierarchy."""

    if issubclass(plugin_class, plugin_base_registry.failure_plugin):
        return [PipelineStage.ERROR]
    if issubclass(plugin_class, plugin_base_registry.resource_plugin):
        return []
    if issubclass(plugin_class, plugin_base_registry.tool_plugin):
        return [PipelineStage.DO]
    if issubclass(plugin_class, plugin_base_registry.prompt_plugin):
        return [PipelineStage.THINK]
    if issubclass(plugin_class, plugin_base_registry.adapter_plugin):
        return [PipelineStage.INPUT, PipelineStage.OUTPUT]
    return []


def configure_plugins(
    base_plugin: Type,
    prompt_plugin: Type,
    adapter_plugin: Type,
    auto_plugin: Type,
    tool_plugin: Type,
    failure_plugin: Type | None = None,
    resource_plugin: Type | None = None,
) -> PluginBaseRegistry:
    """Override the plugin base classes used for auto classification."""

    plugin_base_registry.base_plugin = base_plugin
    plugin_base_registry.prompt_plugin = prompt_plugin
    plugin_base_registry.adapter_plugin = adapter_plugin
    plugin_base_registry.auto_plugin = auto_plugin
    plugin_base_registry.tool_plugin = tool_plugin
    if failure_plugin is not None:
        plugin_base_registry.failure_plugin = failure_plugin
    if resource_plugin is not None:
        plugin_base_registry.resource_plugin = resource_plugin
    return plugin_base_registry


def import_plugin_class(path: str) -> Type:
    """Import a plugin class from ``path``."""

    if ":" in path:
        module_path, class_name = path.split(":", 1)
    elif "." in path:
        module_path, class_name = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid plugin path: {path}")
    module = import_module(module_path)
    return getattr(module, class_name)


class PluginAutoClassifier:
    """Wrap coroutine functions as plugin instances without introspection."""

    @staticmethod
    def classify(
        plugin_func: Any, user_hints: Optional[Dict[str, Any]] | None = None
    ) -> Any:
        """Return a plugin object for ``plugin_func`` using explicit hints."""

        if not inspect.iscoroutinefunction(plugin_func):
            raise TypeError(
                f"Plugin function '{getattr(plugin_func, '__name__', 'unknown')}' must be async"
            )

        hints: Dict[str, Any] = user_hints or {}

        base = hints.get("plugin_class")
        if base is None:
            base = plugin_base_registry.prompt_plugin

        stage_hint = hints.get("stages") or hints.get("stage")
        if stage_hint is not None:
            stages = stage_hint if isinstance(stage_hint, list) else [stage_hint]
            stages = [PipelineStage.from_str(str(s)) for s in stages]
            explicit = True
        else:
            stages = default_stages_for_class(cast(Type, base))
            explicit = False

        name = hints.get("name", plugin_func.__name__)

        plugin_obj = plugin_base_registry.auto_plugin(
            func=plugin_func,
            stages=stages,
            name=name,
            base_class=cast(Type, base),
        )
        plugin_obj._explicit_stages = explicit
        return plugin_obj

    @staticmethod
    def classify_and_route(
        plugin_func: Any, user_hints: Optional[Dict[str, Any]] | None = None
    ) -> Any:
        return PluginAutoClassifier.classify(plugin_func, user_hints)


__all__ = [
    "PluginAutoClassifier",
    "import_plugin_class",
    "configure_plugins",
    "default_stages_for_class",
]
