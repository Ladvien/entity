from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from pipeline.base_plugins import BasePlugin
from pipeline.stages import PipelineStage


class ResourceRegistry:
    """Registry for instantiated resource plugins."""

    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}

    def add(self, name: str, resource: Any) -> None:
        """Register ``resource`` under ``name``."""

        self._resources[name] = resource

    def get(self, name: str) -> Any | None:
        """Return the resource registered as ``name`` if present."""

        return self._resources.get(name)


class ToolRegistry:
    """Registry for tool plugins."""

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}

    def add(self, name: str, tool: Any) -> None:
        """Register ``tool`` under ``name``."""

        self._tools[name] = tool

    def get(self, name: str) -> Any | None:
        """Return the tool registered as ``name`` if present."""

        return self._tools.get(name)


class PluginRegistry:
    """Registry mapping pipeline stages to plugin instances."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[PipelineStage, List[BasePlugin]] = defaultdict(list)
        self._names: Dict[BasePlugin, str] = {}

    def register_plugin_for_stage(
        self, plugin: BasePlugin, stage: PipelineStage | str, name: str | None = None
    ) -> None:
        """Register ``plugin`` to execute during ``stage``."""
        try:
            stage_enum = PipelineStage.ensure(stage)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"Cannot register {plugin.__class__.__name__} for invalid stage '{stage}'"
            ) from exc

        self._stage_plugins[stage_enum].append(plugin)
        self._stage_plugins[stage_enum].sort(key=lambda p: getattr(p, "priority", 50))
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)
        self._names.setdefault(plugin, str(plugin_name))

    def get_for_stage(self, stage: PipelineStage) -> List[BasePlugin]:
        """Return plugins for ``stage`` sorted by ascending priority."""

        return list(self._stage_plugins.get(stage, []))

    def list_plugins(self) -> List[BasePlugin]:
        """Return all registered plugins without duplicates."""

        seen = set()
        plugins: List[BasePlugin] = []
        for stage_list in self._stage_plugins.values():
            for plugin in stage_list:
                if plugin not in seen:
                    seen.add(plugin)
                    plugins.append(plugin)
        return plugins

    def get_plugin_name(self, plugin: BasePlugin) -> str:
        """Return the canonical name for ``plugin``."""

        return self._names.get(plugin, plugin.__class__.__name__)

    def get_dependents(self, dependency_name: str) -> List[BasePlugin]:
        """Return plugins that depend on ``dependency_name``."""

        dependents: List[BasePlugin] = []
        for plugin in self.list_plugins():
            if dependency_name in getattr(plugin, "dependencies", []):
                dependents.append(plugin)
        return dependents


@dataclass
class SystemRegistries:
    """Container for all runtime registries."""

    resources: ResourceRegistry
    tools: ToolRegistry
    plugins: PluginRegistry
