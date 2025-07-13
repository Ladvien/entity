"""Simplified plugin and resource registries."""

from __future__ import annotations

from dataclasses import dataclass
from collections import OrderedDict
from typing import Any, Awaitable, Callable, Dict, List

from entity.core.validation import verify_dependencies, verify_stage_assignment
from entity.pipeline.stages import PipelineStage


@dataclass
class PluginCapabilities:
    """Describe a plugin's declared capabilities."""

    supported_stages: list[str]
    required_resources: list[str]


class PluginRegistry:
    """Register plugins for pipeline stages preserving order and capabilities."""

    def __init__(self) -> None:
        self._stage_plugins: Dict[str, OrderedDict[Any, str]] = {}
        self._names: OrderedDict[Any, str] = OrderedDict()
        self._capabilities: Dict[Any, PluginCapabilities] = {}

    async def register_plugin_for_stage(
        self, plugin: Any, stage: str | PipelineStage, name: str | None = None
    ) -> None:
        stage_enum = PipelineStage.ensure(stage)
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)

        verify_stage_assignment(plugin, stage_enum)
        verify_dependencies(plugin, self._names.values())

        key = str(stage_enum)
        if key not in self._stage_plugins:
            self._stage_plugins[key] = OrderedDict()

        self._stage_plugins[key][plugin] = plugin_name
        self._names[plugin] = plugin_name
        caps = self._capabilities.get(plugin)
        if caps is None:
            deps = list(getattr(plugin, "dependencies", []))
            caps = PluginCapabilities([], deps)
            self._capabilities[plugin] = caps
        if key not in caps.supported_stages:
            caps.supported_stages.append(key)

    async def declare_capabilities(
        self,
        plugin: Any,
        *,
        stages: list[str] | None = None,
        required_resources: list[str] | None = None,
    ) -> None:
        caps = self._capabilities.setdefault(
            plugin,
            PluginCapabilities([], list(getattr(plugin, "dependencies", []))),
        )
        if stages is not None:
            for st in stages:
                if st not in caps.supported_stages:
                    caps.supported_stages.append(st)
        if required_resources is not None:
            for dep in required_resources:
                if dep not in caps.required_resources:
                    caps.required_resources.append(dep)

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

    def get_capabilities(self, plugin: Any) -> PluginCapabilities | None:
        return self._capabilities.get(plugin)

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

            def _match(tool: Any) -> bool:
                declared = getattr(
                    tool, "intents", getattr(tool.__class__, "intents", [])
                )
                return any(i == str(t).lower() for t in declared)

            items = [(k, v) for k, v in items if _match(v)]
        return items


@dataclass
class SystemRegistries:
    resources: Any
    tools: ToolRegistry
    plugins: PluginRegistry
    validators: Any | None = None


__all__ = ["PluginCapabilities", "PluginRegistry", "ToolRegistry", "SystemRegistries"]
