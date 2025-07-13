from __future__ import annotations

"""Utilities for plugin classification and discovery."""

import inspect
from dataclasses import dataclass
from importlib import import_module
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type, cast

from entity.pipeline.utils import _normalize_stages
from entity.core.plugin_analyzer import suggest_upgrade

from entity.utils.logging import get_logger


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

logger = get_logger(__name__)


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
    try:
        module = import_module(module_path)
    except ModuleNotFoundError:
        sys.path.insert(0, str(Path.cwd()))
        sys.path.append(str(Path.cwd() / "src"))
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

        try:
            source = inspect.getsource(plugin_func)
        except OSError:
            lines = 0
        else:
            lines = len(source.splitlines())
            msg = suggest_upgrade(plugin_func)
            if msg:
                logger.warning(msg)
            if lines > 20:
                logger.warning(
                    "Function '%s' is %d lines long; consider using a class-based plugin",
                    plugin_func.__name__,
                    lines,
                )

        hints: Dict[str, Any] = user_hints or {}

        base_cls = hints.get("plugin_class") or plugin_base_registry.prompt_plugin

        stage_hint = hints.get("stages") or hints.get("stage")
        if stage_hint is not None:
            stages = _normalize_stages(stage_hint)
            explicit = True
        else:
            class_value = getattr(cast(Type, base_cls), "stages", None) or getattr(
                cast(Type, base_cls), "stage", None
            )
            stages = _normalize_stages(class_value) if class_value is not None else []
            explicit = False

        name = hints.get("name", plugin_func.__name__)

        plugin_obj = plugin_base_registry.auto_plugin(
            func=plugin_func,
            stages=stages,
            name=name,
            base_class=cast(Type, base_cls),
        )
        plugin_obj.config["stages" if len(plugin_obj.stages) > 1 else "stage"] = (
            plugin_obj.stages if len(plugin_obj.stages) > 1 else plugin_obj.stages[0]
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
]
