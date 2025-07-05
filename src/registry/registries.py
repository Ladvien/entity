from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List
import asyncio

from pipeline.stages import PipelineStage
from pipeline.user_plugins import BasePlugin


class ResourceRegistry:
    """Registry for instantiated resource plugins."""

    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def add(self, name: str, resource: Any) -> None:
        """Register ``resource`` under ``name``."""

        async with self._lock:
            self._resources[name] = resource

    async def add_from_config(self, name: str, cls: type, config: Dict) -> None:
        """Instantiate ``cls`` from ``config`` and register it."""

        if hasattr(cls, "from_config"):
            instance = cls.from_config(config)
        else:
            instance = cls(config)
        await self.add(getattr(instance, "name", name), instance)

    def get(self, name: str) -> Any | None:
        """Return the resource registered as ``name`` if present."""

        return self._resources.get(name)

    async def remove(self, name: str) -> None:
        async with self._lock:
            self._resources.pop(name, None)


class ToolRegistry:
    """Registry for tool plugins."""

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def add(self, name: str, tool: Any) -> None:
        """Register ``tool`` under ``name``."""

        async with self._lock:
            self._tools[name] = tool

    def get(self, name: str) -> Any | None:
        """Return the tool registered as ``name`` if present."""

        return self._tools.get(name)


class PluginRegistry:
    """Registry mapping pipeline stages to plugin instances."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[PipelineStage, List[BasePlugin]] = defaultdict(list)
        self._names: Dict[BasePlugin, str] = {}
        self._plugins_by_name: Dict[str, BasePlugin] = {}
        self._dependents: Dict[str, List[BasePlugin]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def register_plugin_for_stage(
        self, plugin: BasePlugin, stage: PipelineStage | str, name: str | None = None
    ) -> None:
        """Register ``plugin`` to execute during ``stage``."""
        try:
            stage = PipelineStage(stage)
        except ValueError as exc:
            raise ValueError(f"Invalid stage: {stage}") from exc
        async with self._lock:
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
