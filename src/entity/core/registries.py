from __future__ import annotations

"""Simplified plugin and resource registries."""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List


class PluginRegistry:
    """Register plugins for each pipeline stage."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[str, List[Any]] = {}
        self._names: Dict[Any, str] = {}

    async def register_plugin_for_stage(
        self, plugin: Any, stage: str, name: str
    ) -> None:
        self._stage_plugins.setdefault(stage, []).append(plugin)
        self._names[plugin] = name

    def get_plugins_for_stage(self, stage: str) -> List[Any]:
        return list(self._stage_plugins.get(stage, []))

    def list_plugins(self) -> List[Any]:
        plugins: List[Any] = []
        for plist in self._stage_plugins.values():
            plugins.extend(plist)
        return plugins

    def get_plugin_name(self, plugin: Any) -> str:
        return self._names.get(plugin, plugin.__class__.__name__)


class ToolRegistry:
    """Store registered tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Awaitable[Any]]] = {}

    async def add(self, name: str, tool: Callable[..., Awaitable[Any]]) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Callable[..., Awaitable[Any]] | None:
        return self._tools.get(name)


@dataclass
class SystemRegistries:
    resources: Any
    tools: ToolRegistry
    plugins: PluginRegistry
