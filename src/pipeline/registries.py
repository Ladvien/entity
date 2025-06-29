from __future__ import annotations

from typing import Any, Dict, List


class ResourceRegistry:
    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}

    def add_resource(self, resource: Any) -> None:
        self._resources[resource.name] = resource

    def get(self, name: str) -> Any | None:
        return self._resources.get(name)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}

    def add_tool(self, tool: Any) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Any | None:
        return self._tools.get(name)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins_by_stage: Dict[Any, List[Any]] = {}

    def register_plugin_for_stage(self, plugin: Any, stage: Any, name: str) -> None:
        self._plugins_by_stage.setdefault(stage, []).append(plugin)

    def get_for_stage(self, stage: Any) -> List[Any]:
        return self._plugins_by_stage.get(stage, [])
