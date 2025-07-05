from __future__ import annotations

import asyncio
import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional
import asyncio

from registry import PluginRegistry, ResourceRegistry, SystemRegistries, ToolRegistry

from .base_plugins import BasePlugin
from .interfaces import PluginAutoClassifier
from .logging import get_logger
from .runtime import AgentRuntime

logger = get_logger(__name__)

PLUGIN_CACHE_FILE = "plugins.json"


@dataclass
class AgentBuilder:
    """Collect plugins and build :class:`AgentRuntime`."""

    plugin_registry: PluginRegistry = field(default_factory=PluginRegistry)
    resource_registry: ResourceRegistry = field(default_factory=ResourceRegistry)
    tool_registry: ToolRegistry = field(default_factory=ToolRegistry)

    # ------------------------------ plugin utils ------------------------------
    async def add_plugin(self, plugin: BasePlugin) -> None:
        if not hasattr(plugin, "_execute_impl") or not callable(
            getattr(plugin, "_execute_impl")
        ):
            name = getattr(plugin, "name", plugin.__class__.__name__)
            raise TypeError(f"Plugin '{name}' must implement async '_execute_impl'")
        for stage in getattr(plugin, "stages", []):
            name = getattr(plugin, "name", plugin.__class__.__name__)
            await self.plugin_registry.register_plugin_for_stage(plugin, stage, name)

    def plugin(self, func: Optional[Callable] = None, **hints):
        """Decorator registering ``func`` as a plugin."""

        def decorator(f: Callable) -> Callable:
            plugin = PluginAutoClassifier.classify(f, hints)
            coro = self.add_plugin(plugin)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(coro)
            else:
                loop.create_task(coro)
            return f

        return decorator(func) if func else decorator

    # ---------------------------- discovery helpers ---------------------------
    @classmethod
    def from_directory(cls, directory: str) -> "AgentBuilder":
        builder = cls()
        builder.load_plugins_from_directory(directory)
        return builder

    @classmethod
    def from_package(cls, package_name: str) -> "AgentBuilder":
        builder = cls()
        builder.load_plugins_from_package(package_name)
        return builder

    def load_plugins_from_directory(self, directory: str) -> None:
        async def _load() -> None:
            path = Path(directory)
            cache = path / PLUGIN_CACHE_FILE
            plugin_files: list[Path] = []
            plugins: list[BasePlugin] = []

            if cache.exists():
                try:
                    data = json.loads(cache.read_text())
                    plugin_files = [Path(p) for p in data.get("files", [])]
                except Exception:  # noqa: BLE001
                    plugin_files = []

            discovered: list[Path] = []
            if not plugin_files:
                for file in path.glob("*.py"):
                    if file.name.startswith("_"):
                        continue
                    module = await self._import_module(file)
                    if module is None:
                        continue
                    found = self._collect_module_plugins(module)
                    if found:
                        plugins.extend(found)
                        discovered.append(file)
                cache.write_text(json.dumps({"files": [str(f) for f in discovered]}))
                plugin_files = discovered
            else:
                for file in plugin_files:
                    module = await self._import_module(file)
                    if module is not None:
                        plugins.extend(self._collect_module_plugins(module))

            self._register_plugins(plugins)

        asyncio.run(_load())

    def load_plugins_from_package(self, package_name: str) -> None:
        async def _load() -> None:
            import pkgutil

            cache_dir = Path(".plugin_cache")
            cache_dir.mkdir(exist_ok=True)
            cache = cache_dir / f"{package_name.replace('.', '_')}_{PLUGIN_CACHE_FILE}"

            modules: list[str] = []
            plugins: list[BasePlugin] = []

            if cache.exists():
                try:
                    data = json.loads(cache.read_text())
                    modules = list(data.get("modules", []))
                except Exception:  # noqa: BLE001
                    modules = []

            if not modules:
                package = importlib.import_module(package_name)
                if not hasattr(package, "__path__"):
                    mod = await self._import_module_name(package_name)
                    if mod is not None:
                        plugins.extend(self._collect_module_plugins(mod))
                        modules = [package_name]
                else:
                    for info in pkgutil.walk_packages(
                        package.__path__, prefix=package.__name__ + "."
                    ):
                        mod = await self._import_module_name(info.name)
                        if mod is None:
                            continue
                        found = self._collect_module_plugins(mod)
                        if found:
                            plugins.extend(found)
                            modules.append(info.name)
                cache.write_text(json.dumps({"modules": modules}))
            else:
                for name in modules:
                    mod = await self._import_module_name(name)
                    if mod is not None:
                        plugins.extend(self._collect_module_plugins(mod))

            self._register_plugins(plugins)

        asyncio.run(_load())

    # ------------------------------ runtime build -----------------------------
    def build_runtime(self) -> "AgentRuntime":
        registries = SystemRegistries(
            resources=self.resource_registry,
            tools=self.tool_registry,
            plugins=self.plugin_registry,
        )
        return AgentRuntime(registries)

    # ------------------------------ internals --------------------------------
    def _import_module_sync(self, file: Path) -> ModuleType | None:
        import importlib.util

        try:
            spec = importlib.util.spec_from_file_location(file.stem, file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            raise ImportError(f"Cannot load spec for {file}")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to import plugin module %s: %s", file, exc)
            return None

    async def _import_module(self, file: Path) -> ModuleType | None:
        return await asyncio.to_thread(self._import_module_sync, file)

    def _import_module_name_sync(self, name: str) -> ModuleType | None:
        try:
            return importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to import plugin module %s: %s", name, exc)
            return None

    async def _import_module_name(self, name: str) -> ModuleType | None:
        return await asyncio.to_thread(self._import_module_name_sync, name)

    def _register_plugins(self, plugins: list[BasePlugin]) -> None:
        from pipeline.utils.dependency_graph import DependencyGraph

        graph = {}
        plugin_map = {}
        for plugin in plugins:
            name = getattr(plugin, "name", plugin.__class__.__name__)
            plugin_map[name] = plugin
            graph[name] = list(getattr(plugin, "dependencies", []))

        order = DependencyGraph(graph).topological_sort()
        for name in order:
            plugin = plugin_map[name]
            for stage in getattr(plugin, "stages", []):
                self.plugin_registry.register_plugin_for_stage(plugin, stage, name)

    def _collect_module_plugins(self, module: ModuleType) -> list[BasePlugin]:
        import inspect

        found: list[BasePlugin] = []
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            try:
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                ):
<<<<<<< HEAD
                    found.append(obj({}))
=======
                    asyncio.run(self.add_plugin(obj({})))
>>>>>>> c43ef0c5ea6ac8f5728552a9386d6e348575c75f
                elif callable(obj) and name.endswith("_plugin"):
                    plugin = PluginAutoClassifier.classify(obj, {})
                    found.append(plugin)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to register plugin from %s.%s: %s",
                    module.__name__,
                    name,
                    exc,
                )
                continue

        return found
