"""Simplified plugin and resource registries."""

from __future__ import annotations

from dataclasses import dataclass
from collections import OrderedDict
from typing import Any, Awaitable, Callable, Dict, List


class PluginRegistry:
    """Register plugins for each pipeline stage preserving insertion order."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[str, OrderedDict[Any, str]] = {}
        self._names: "OrderedDict[Any, str]" = OrderedDict()

    async def register_plugin_for_stage(
        self, plugin: Any, stage: str, name: str | None = None
    ) -> None:
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)
        if stage not in self._stage_plugins:
            self._stage_plugins[stage] = OrderedDict()
        self._stage_plugins[stage][plugin] = plugin_name
        if plugin not in self._names:
            self._names[plugin] = plugin_name

    def get_plugins_for_stage(self, stage: str) -> List[Any]:
        plugins = self._stage_plugins.get(stage)
        if plugins is None:
            return []
        return list(plugins.keys())

    def get_plugin(self, name: str) -> Any | None:
        """Return the plugin registered with ``name``."""
        for plugin, plugin_name in self._names.items():
            if plugin_name == name:
                return plugin
        return None

    # Backward compatibility for older API
    def get_by_name(self, name: str) -> Any | None:
        return self.get_plugin(name)

    def list_plugins(self) -> List[Any]:
        return list(self._names.keys())

    def get_plugin_name(self, plugin: Any) -> str:
        name = self._names.get(plugin)
        return name if name is not None else plugin.__class__.__name__


class ToolRegistry:
    """Store registered tools and handle discovery."""

    def __init__(self, *, concurrency_limit: int = 5) -> None:
        self._tools: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.concurrency_limit = concurrency_limit

    async def add(self, name: str, tool: Callable[..., Awaitable[Any]]) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Callable[..., Awaitable[Any]] | None:
        return self._tools.get(name)

    def discover(
        self, *, name: str | None = None, intent: str | None = None
    ) -> list[tuple[str, Any]]:
        """Return tools filtered by ``name`` or ``intent``."""
        items = list(self._tools.items())
        if name is not None:
            n = name.lower()
            items = [(k, v) for k, v in items if n in k.lower()]
        if intent is not None:
            i = intent.lower()
            items = [
                (k, v)
                for k, v in items
                if any(i in t.lower() for t in getattr(v, "intents", []))
            ]
        return items


@dataclass
class SystemRegistries:
    resources: Any
    tools: ToolRegistry
    plugins: PluginRegistry
    validators: Any | None = None
