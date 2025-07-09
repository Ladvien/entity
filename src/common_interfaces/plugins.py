"""Defines common plugin interfaces."""

import inspect
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, Optional, Type, cast


@dataclass
class PluginBaseRegistry:
    """Container for plugin base classes used across the system."""

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
    """Configure concrete plugin base classes used for auto classification."""

    global plugin_base_registry
    plugin_base_registry.base_plugin = base_plugin
    plugin_base_registry.prompt_plugin = prompt_plugin
    plugin_base_registry.adapter_plugin = adapter_plugin
    plugin_base_registry.auto_plugin = auto_plugin
    return plugin_base_registry


def import_plugin_class(path: str) -> Type:
    """Import plugin class from ``path``."""
    if ":" in path:
        module_path, class_name = path.split(":", 1)
    elif "." in path:
        module_path, class_name = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid plugin path: {path}")
    module = import_module(module_path)
    return getattr(module, class_name)


class PluginAutoClassifier:
    """Utility to generate plugin classes from async functions."""

    @staticmethod
    def classify(
        plugin_func: Any, user_hints: Optional[Dict[str, Any]] | None = None
    ) -> Any:
        """Return a generated plugin class for ``plugin_func``."""

        from pipeline.stages import PipelineStage

        if not inspect.iscoroutinefunction(plugin_func):
            raise TypeError(
                f"Plugin function '{getattr(plugin_func, '__name__', 'unknown')}' must be async"
            )

        hints = user_hints or {}
        try:
            source = inspect.getsource(plugin_func)
        except OSError:
            source = ""

        if any(k in source for k in ["think", "reason", "analyze"]):
            base = cast(Type, plugin_base_registry.prompt_plugin)
        elif any(k in source for k in ["parse", "validate", "check"]):
            base = cast(Type, plugin_base_registry.adapter_plugin)
        elif any(k in source for k in ["return", "response", "answer"]):
            base = cast(Type, plugin_base_registry.prompt_plugin)
        else:
            base = cast(Type, plugin_base_registry.prompt_plugin)

        def _default_stages(plugin_base: Type) -> list[PipelineStage]:
            from pipeline.base_plugins import AdapterPlugin, PromptPlugin, ToolPlugin

            if issubclass(plugin_base, ToolPlugin):
                return [PipelineStage.DO]
            if issubclass(plugin_base, PromptPlugin):
                return [PipelineStage.THINK]
            if issubclass(plugin_base, AdapterPlugin):
                return [PipelineStage.PARSE, PipelineStage.DELIVER]
            return []

        explicit = False
        inferred = True
        stages = _default_stages(base)
        if "stage" in hints or "stages" in hints:
            hint = hints.get("stages") or hints.get("stage")
            stages = hint if isinstance(hint, list) else [hint]
            stages = [PipelineStage.from_str(str(s)) for s in stages]
            explicit = True
            inferred = False

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
        plugin_obj._type_default_stages = _default_stages(base)
        plugin_obj._inferred = inferred
        return plugin_obj

    @staticmethod
    def classify_and_route(
        plugin_func: Any, user_hints: Optional[Dict[str, Any]] | None = None
    ) -> Any:
        return PluginAutoClassifier.classify(plugin_func, user_hints)


__all__ = ["PluginAutoClassifier", "import_plugin_class"]
