from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from .plugins import BasePlugin
from .stages import PipelineStage


class PluginRegistry:
    def __init__(self) -> None:
        self._stage_plugins: Dict[PipelineStage, List[BasePlugin]] = defaultdict(list)
        self._names: Dict[BasePlugin, str] = {}

    def register_plugin_for_stage(
        self, plugin: BasePlugin, stage: PipelineStage
    ) -> None:
        self._stage_plugins[stage].append(plugin)
        self._stage_plugins[stage].sort(key=lambda p: getattr(p, "priority", 50))
        self._names.setdefault(
            plugin, getattr(plugin, "name", plugin.__class__.__name__)
        )

    def get_for_stage(self, stage: PipelineStage) -> List[BasePlugin]:
        return list(self._stage_plugins.get(stage, []))

    def list_plugins(self) -> List[BasePlugin]:
        seen = set()
        plugins: List[BasePlugin] = []
        for stage_list in self._stage_plugins.values():
            for plugin in stage_list:
                if plugin not in seen:
                    seen.add(plugin)
                    plugins.append(plugin)
        return plugins

    def get_plugin_name(self, plugin: BasePlugin) -> str:
        return self._names.get(plugin, plugin.__class__.__name__)

    def get_dependents(self, dependency_name: str) -> List[BasePlugin]:
        dependents: List[BasePlugin] = []
        for plugin in self.list_plugins():
            if dependency_name in getattr(plugin, "dependencies", []):
                dependents.append(plugin)
        return dependents


class ResourceRegistry:
    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}

    def add(self, name: str, resource: Any) -> None:
        self._resources[name] = resource

    def get(self, name: str) -> Any | None:
        return self._resources.get(name)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}

    def add(self, name: str, tool: Any) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Any | None:
        return self._tools.get(name)
