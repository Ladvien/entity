from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypeVar, cast

from pipeline.base_plugins import BasePlugin
from pipeline.stages import PipelineStage


T = TypeVar("T")


class ResourceRegistry:
    """Registry for instantiated resource plugins."""

    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}

    def add(self, name: str, resource: Any) -> None:
        """Register ``resource`` under ``name``."""

        self._resources[name] = resource

    def add_from_config(self, name: str, cls: type, config: Dict) -> None:
        """Instantiate ``cls`` from ``config`` and register it."""

        if hasattr(cls, "from_config"):
            instance = cls.from_config(config)
        else:
            instance = cls(config)
        self.add(getattr(instance, "name", name), instance)

    def get(self, name: str) -> Optional[T]:
        """Return the resource registered as ``name`` if present."""

        return cast(Optional[T], self._resources.get(name))

    def remove(self, name: str) -> None:
        self._resources.pop(name, None)


class ToolRegistry:
    """Registry for tool plugins."""

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}

    def add(self, name: str, tool: Any) -> None:
        """Register ``tool`` under ``name``."""

        self._tools[name] = tool

    def get(self, name: str) -> Optional[T]:
        """Return the tool registered as ``name`` if present."""

        return cast(Optional[T], self._tools.get(name))


class PluginRegistry:
    """Registry mapping pipeline stages to plugin instances."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[PipelineStage, List[BasePlugin]] = defaultdict(list)
        self._names: Dict[BasePlugin, str] = {}
        self._plugins_by_name: Dict[str, BasePlugin] = {}
        self._dependents: Dict[str, List[BasePlugin]] = defaultdict(list)

    def register_plugin_for_stage(
        self, plugin: BasePlugin, stage: PipelineStage | str, name: str | None = None
    ) -> None:
        """Register ``plugin`` to execute during ``stage``."""
        try:
            stage = PipelineStage(stage)
        except ValueError as exc:
            raise ValueError(f"Invalid stage: {stage}") from exc
        plugins = self._stage_plugins[stage]
        insert_at = len(plugins)
        for idx, existing in enumerate(plugins):
            if plugin.priority < existing.priority:
                insert_at = idx
                break
        plugins.insert(insert_at, plugin)

        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)
        self._names[plugin] = plugin_name
        self._plugins_by_name[plugin_name] = plugin

        for dep in getattr(plugin, "dependencies", []):
            self._dependents.setdefault(dep, []).append(plugin)

    def get_plugins_for_stage(self, stage: PipelineStage) -> List[BasePlugin]:
        """Return list of plugins registered for ``stage``."""

        return self._stage_plugins.get(stage, [])

    def list_plugins(self) -> List[BasePlugin]:
        plugins: List[BasePlugin] = []
        for plist in self._stage_plugins.values():
            plugins.extend(plist)
        return plugins

    def get_plugin_name(self, plugin: BasePlugin) -> str:
        return self._names.get(plugin, plugin.__class__.__name__)

    def get_dependents(self, plugin_name: str) -> List[BasePlugin]:
        return self._dependents.get(plugin_name, [])

    def get_name(self, plugin: BasePlugin) -> str | None:
        """Return registered name for ``plugin`` if any."""

        return self._names.get(plugin)


@dataclass
class SystemRegistries:
    resources: ResourceRegistry
    tools: ToolRegistry
    plugins: PluginRegistry
