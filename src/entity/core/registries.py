from __future__ import annotations

"""Simplified plugin and resource registries."""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List
import time


class PluginRegistry:
    """Register plugins for each pipeline stage."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[str, List[Any]] = {}
        self._names: Dict[Any, str] = {}

    async def register_plugin_for_stage(
        self, plugin: Any, stage: str, name: str | None = None
    ) -> None:
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)
        self._stage_plugins.setdefault(stage, []).append(plugin)
        self._names[plugin] = plugin_name

    def get_plugins_for_stage(self, stage: str) -> List[Any]:
        return list(self._stage_plugins.get(stage, []))

    def get_plugin(self, name: str) -> Any | None:
        """Return the plugin registered with ``name``."""
        for plugin, plugin_name in self._names.items():
            if plugin_name == name:
                return plugin
        return None

    def list_plugins(self) -> List[Any]:
        plugins: List[Any] = []
        for plist in self._stage_plugins.values():
            plugins.extend(plist)
        return plugins

    def get_plugin_name(self, plugin: Any) -> str:
        name = self._names.get(plugin)
        return name if name is not None else plugin.__class__.__name__


class ToolRegistry:
    """Store registered tools with basic caching and discovery."""

    def __init__(
        self, *, concurrency_limit: int = 5, cache_ttl: int | None = None
    ) -> None:
        self._tools: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.concurrency_limit = concurrency_limit
        self.cache_ttl = cache_ttl
        self._cache: Dict[tuple[str, frozenset[tuple[str, Any]]], tuple[Any, float]] = (
            {}
        )

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

    async def get_cached_result(self, name: str, params: Dict[str, Any]) -> Any | None:
        if self.cache_ttl is None:
            return None
        key = (name, frozenset(params.items()))
        item = self._cache.get(key)
        if not item:
            return None
        result, timestamp = item
        if time.time() - timestamp > self.cache_ttl:
            self._cache.pop(key, None)
            return None
        return result

    async def cache_result(
        self, name: str, params: Dict[str, Any], result: Any
    ) -> None:
        if self.cache_ttl is None:
            return
        key = (name, frozenset(params.items()))
        self._cache[key] = (result, time.time())


@dataclass
class SystemRegistries:
    resources: Any
    tools: ToolRegistry
    plugins: PluginRegistry
    validators: Any | None = None
