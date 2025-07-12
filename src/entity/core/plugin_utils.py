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


plugin_base_registry = PluginBaseRegistry()


def default_stages_for_class(plugin_class: Type) -> list[PipelineStage]:
    """Return default stages based on plugin class hierarchy."""

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
) -> PluginBaseRegistry:
    """Override the plugin base classes used for auto classification."""

    plugin_base_registry.base_plugin = base_plugin
    plugin_base_registry.prompt_plugin = prompt_plugin
    plugin_base_registry.adapter_plugin = adapter_plugin
    plugin_base_registry.auto_plugin = auto_plugin
    plugin_base_registry.tool_plugin = tool_plugin
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
    """Generate plugin classes from async functions."""

    @staticmethod
    def classify(
        plugin_func: Any, user_hints: Optional[Dict[str, Any]] | None = None
    ) -> Any:
        """Return a plugin object for ``plugin_func``."""

        if not inspect.iscoroutinefunction(plugin_func):
            raise TypeError(
                f"Plugin function '{getattr(plugin_func, '__name__', 'unknown')}' must be async"
            )

        hints = user_hints or {}
        try:
            source = inspect.getsource(plugin_func)
        except OSError:
            source = ""

        sig = inspect.signature(plugin_func)
        param_names = [p.name.lower() for p in sig.parameters.values()]

        action_keywords = {"action", "tool", "command"}
        named_like_tool = any(
            any(key in name for key in action_keywords) for name in param_names[1:]
        )

        calls_tool = any(k in source for k in ["tool_use(", "queue_tool_use("])

        if calls_tool or named_like_tool:
            base = cast(Type, plugin_base_registry.tool_plugin)
        elif any(k in source for k in ["think", "reason", "analyze"]):
            base = cast(Type, plugin_base_registry.prompt_plugin)
        elif any(k in source for k in ["parse", "validate", "check"]):
            base = cast(Type, plugin_base_registry.adapter_plugin)
        elif any(k in source for k in ["return", "response", "answer"]):
            base = cast(Type, plugin_base_registry.prompt_plugin)
        else:
            base = cast(Type, plugin_base_registry.prompt_plugin)

        explicit = False
        inferred = False
        stages = default_stages_for_class(base)
        if "stage" in hints or "stages" in hints:
            hint = hints.get("stages") or hints.get("stage")
            stages = hint if isinstance(hint, list) else [hint]
            stages = [PipelineStage.from_str(str(s)) for s in stages]
            explicit = True
        else:
            inferred = True

        name = hints.get("name", plugin_func.__name__)

        plugin_obj = plugin_base_registry.auto_plugin(
            func=plugin_func,
            stages=stages,
            name=name,
            base_class=base,
        )
        plugin_obj._explicit_stages = explicit
        plugin_obj._inferred_stages = inferred
        plugin_obj._auto_inferred_stages = inferred
        plugin_obj._type_default_stages = default_stages_for_class(base)
        plugin_obj._inferred = inferred
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
