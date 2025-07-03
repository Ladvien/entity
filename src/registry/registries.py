from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from pipeline.plugins import BasePlugin
from pipeline.stages import PipelineStage


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

    def get(self, name: str) -> Any | None:
        """Return the resource registered as ``name`` if present."""

        return self._resources.get(name)

    def names(self) -> list[str]:
        """Return the names of all registered resources."""

        return list(self._resources.keys())


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
            stage = PipelineStage(stage)
        except ValueError as exc:
            raise ValueError(f"Invalid stage: {stage}") from exc
        self._stage_plugins[stage].append(plugin)
        if name:
            self._names[plugin] = name

    def get_plugins_for_stage(self, stage: PipelineStage) -> List[BasePlugin]:
        """Return list of plugins registered for ``stage``."""

        return self._stage_plugins.get(stage, [])

    def get_name(self, plugin: BasePlugin) -> str | None:
        """Return registered name for ``plugin`` if any."""

        return self._names.get(plugin)


@dataclass
class SystemRegistries:
    resources: ResourceRegistry
    tools: ToolRegistry
    plugins: PluginRegistry
