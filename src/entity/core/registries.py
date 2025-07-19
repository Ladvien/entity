from __future__ import annotations

from dataclasses import dataclass
from collections import OrderedDict
from typing import Any, Awaitable, Callable, Dict, List
import logging
import asyncio
import inspect

from entity.core.resources.container import DependencyGraph
from entity.core.validation import verify_stage_assignment

from entity.pipeline.stages import PipelineStage


logger = logging.getLogger(__name__)


@dataclass
class PluginCapabilities:
    """Describe a plugin's declared capabilities."""

    supported_stages: list[str]
    required_resources: list[str]


class PluginRegistry:
    """Register plugins for each pipeline stage preserving insertion order and track capabilities."""

    def __init__(self) -> None:
        self._stage_plugins: "OrderedDict[str, OrderedDict[Any, str]]" = OrderedDict()
        self._names: "OrderedDict[Any, str]" = OrderedDict()
        self._plugins_by_name: "OrderedDict[str, Any]" = OrderedDict()
        self._configs: Dict[str, Dict] = {}
        self._capabilities: Dict[Any, PluginCapabilities] = {}

    async def register_plugin_for_stage(
        self, plugin: Any, stage: str | PipelineStage, name: str | None = None
    ) -> None:
        stage_enum = PipelineStage.ensure(stage)
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)
        validator = getattr(plugin, "validate_registration_stage", None)
        if callable(validator):
            validator(stage_enum)
        verify_stage_assignment(plugin, stage_enum)

        key = str(stage_enum)
        if key not in self._stage_plugins:
            self._stage_plugins[key] = OrderedDict()
        self._stage_plugins[key][plugin] = plugin_name
        logger.debug(
            "Registered plugin %s for stage %s at position %d",
            plugin_name,
            key,
            len(self._stage_plugins[key]),
        )
        if plugin not in self._names:
            self._names[plugin] = plugin_name
        if plugin_name not in self._plugins_by_name:
            self._plugins_by_name[plugin_name] = plugin
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

    def register_plugin(
        self,
        plugin: Any,
        name: str,
        *,
        dependencies: list[str] | None = None,
        config: Dict | None = None,
    ) -> None:
        """Register a plugin class for dependency validation."""

        if name in self._plugins_by_name:
            return
        self._plugins_by_name[name] = plugin
        self._names[plugin] = name
        self._configs[name] = config or {}
        deps = (
            dependencies
            if dependencies is not None
            else list(getattr(plugin, "dependencies", []))
        )
        self._capabilities[plugin] = PluginCapabilities([], list(deps))

    def get_class(self, name: str) -> Any | None:
        return self._plugins_by_name.get(name)

    def get_config(self, name: str) -> Dict | None:
        return self._configs.get(name)

    def list_plugin_names(self) -> List[str]:
        return list(self._plugins_by_name.keys())

    def dependency_graph(self) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {n: [] for n in self._plugins_by_name}
        for plugin, caps in self._capabilities.items():
            src = self._names.get(plugin)
            if src is None:
                continue
            for dep in caps.required_resources:
                dep_name = dep[:-1] if dep.endswith("?") else dep
                if dep_name in graph:
                    graph[dep_name].append(src)
        return graph

    def validate_dependencies(self) -> None:
        names = set(self._plugins_by_name)
        for plugin in self._plugins_by_name.values():
            caps = self._capabilities.get(plugin)
            deps = (
                caps.required_resources
                if caps is not None
                else list(getattr(plugin, "dependencies", []))
            )
            plugin_name = getattr(plugin, "name", plugin.__class__.__name__)
            for dep in deps:
                optional = str(dep).endswith("?")
                dep_name = str(dep)[:-1] if optional else str(dep)
                if dep_name == plugin_name:
                    raise SystemError(f"Plugin '{plugin_name}' cannot depend on itself")
                if dep_name not in names and not optional:
                    available = ", ".join(sorted(names))
                    raise SystemError(
                        f"Plugin '{plugin_name}' requires '{dep_name}' but it's not registered. Available: {available}"
                    )
            validator = getattr(plugin, "validate_dependencies", None)
            if callable(validator):
                result = validator(self)
                if inspect.isawaitable(result):
                    result = asyncio.run(result)
                if not result.success:
                    raise SystemError(
                        f"Dependency validation failed for {plugin.__name__}: {result.message}"
                    )
        DependencyGraph(self.dependency_graph()).topological_sort()

    def get_plugins_for_stage(self, stage: str | PipelineStage) -> List[Any]:
        stage_key = stage if isinstance(stage, str) else str(stage)
        plugins = self._stage_plugins.get(stage_key)
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

    def has_plugin(self, name: str) -> bool:
        """Return ``True`` if a plugin registered under ``name`` exists."""

        return name in self._plugins_by_name

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
        """Return tools filtered by ``name`` or ``intent``.

        When multiple tools share an intent and at least one lists that intent as
        its only capability, tools that also list it first but not exclusively
        are dropped. Tools where the intent appears later are always kept.
        """

        items = list(self._tools.items())
        if name is not None:
            n = name.lower()
            items = [(k, v) for k, v in items if n in k.lower()]

        if intent is not None:
            normalized = intent.lower()
            enriched: list[tuple[str, Any, list[str]]] = []
            for key, tool in items:
                declared = getattr(
                    tool, "intents", getattr(tool.__class__, "intents", [])
                )
                intents = [str(t).lower() for t in declared]
                if normalized in intents:
                    enriched.append((key, tool, intents))

            has_primary = any(
                intents and len(intents) == 1 and intents[0] == normalized
                for _, _, intents in enriched
            )

            if has_primary:
                enriched = [
                    (k, v, ints)
                    for k, v, ints in enriched
                    if not (ints and ints[0] == normalized and len(ints) > 1)
                ]

            items = [(k, v) for k, v, _ in enriched]

        return items


@dataclass
class SystemRegistries:
    resources: Any
    tools: ToolRegistry
    plugins: PluginRegistry
    validators: Any | None = None


__all__ = ["PluginCapabilities", "PluginRegistry", "ToolRegistry", "SystemRegistries"]
