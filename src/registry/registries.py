from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from pipeline.base_plugins import BasePlugin
from pipeline.resources.container import ResourceContainer
from pipeline.stages import PipelineStage


class ToolRegistry:
    """Registry for tool plugins with optional result caching."""

    def __init__(
        self,
        *,
        concurrency_limit: int = 5,
        cache_ttl: int | None = None,
    ) -> None:
        self.concurrency_limit = concurrency_limit
        self._cache_ttl = cache_ttl
        self._tools: Dict[str, Any] = {}
        self._cache: Dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    async def add(self, name: str, tool: Any) -> None:
        """Register ``tool`` under ``name``."""

        async with self._lock:
            self._tools[name] = tool

    def get(self, name: str) -> Any | None:
        """Return the tool registered as ``name`` if present."""

        return self._tools.get(name)

    async def get_cached_result(self, name: str, params: Dict[str, Any]) -> Any | None:
        if self._cache_ttl is None:
            return None
        key = self._make_cache_key(name, params)
        async with self._lock:
            item = self._cache.get(key)
            if not item:
                return None
            value, expires = item
            if expires and expires < time.time():
                del self._cache[key]
                return None
            return value

    async def cache_result(
        self, name: str, params: Dict[str, Any], result: Any
    ) -> None:
        if self._cache_ttl is None:
            return
        key = self._make_cache_key(name, params)
        expire_at = None
        if self._cache_ttl > 0:
            expire_at = time.time() + self._cache_ttl
        async with self._lock:
            self._cache[key] = (result, expire_at)

    @staticmethod
    def _make_cache_key(name: str, params: Dict[str, Any]) -> str:
        import hashlib
        import json

        params_repr = json.dumps(params, sort_keys=True)
        return hashlib.sha256(f"{name}:{params_repr}".encode()).hexdigest()


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
    resources: ResourceContainer
    tools: ToolRegistry
    plugins: PluginRegistry
