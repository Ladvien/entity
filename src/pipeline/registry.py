from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .plugins import BasePlugin
from .stages import PipelineStage

class PluginRegistry:
    def __init__(self):
        self._stage_plugins: Dict[PipelineStage, List[BasePlugin]] = defaultdict(list)

    def register_plugin_for_stage(self, plugin: BasePlugin, stage: PipelineStage):
        self._stage_plugins[stage].append(plugin)
        self._stage_plugins[stage].sort(key=lambda p: getattr(p, "priority", 50))

    def get_for_stage(self, stage: PipelineStage) -> List[BasePlugin]:
        return list(self._stage_plugins.get(stage, []))


class ResourceRegistry:
    def __init__(self):
        self._resources: Dict[str, any] = {}

    def add(self, name: str, resource: any):
        self._resources[name] = resource

    def get(self, name: str):
        return self._resources.get(name)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, any] = {}

    def add(self, name: str, tool: any):
        self._tools[name] = tool

    def get(self, name: str):
        return self._tools.get(name)
