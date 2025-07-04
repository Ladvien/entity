from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional

from .logging import get_logger

from registry import PluginRegistry, ResourceRegistry, SystemRegistries, ToolRegistry

from .plugins import BasePlugin, PluginAutoClassifier
from .runtime import AgentRuntime
from .stages import PipelineStage


logger = get_logger(__name__)


@dataclass
class AgentBuilder:
    """Collect plugins and build :class:`AgentRuntime`."""

    plugin_registry: PluginRegistry = field(default_factory=PluginRegistry)
    resource_registry: ResourceRegistry = field(default_factory=ResourceRegistry)
    tool_registry: ToolRegistry = field(default_factory=ToolRegistry)

    # ------------------------------ plugin utils ------------------------------
    def add_plugin(self, plugin: BasePlugin) -> None:
        if not hasattr(plugin, "_execute_impl") or not callable(
            getattr(plugin, "_execute_impl")
        ):
            name = getattr(plugin, "name", plugin.__class__.__name__)
            raise TypeError(f"Plugin '{name}' must implement async '_execute_impl'")
        for stage in getattr(plugin, "stages", []):
            name = getattr(plugin, "name", plugin.__class__.__name__)
            self.plugin_registry.register_plugin_for_stage(plugin, stage, name)

    def plugin(self, func: Optional[Callable] = None, **hints):
        """Decorator registering ``func`` as a plugin."""

        def decorator(f: Callable) -> Callable:
            plugin = PluginAutoClassifier.classify(f, hints)
            self.add_plugin(plugin)
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
        for file in Path(directory).glob("*.py"):
            if file.name.startswith("_"):
                continue
            module = self._import_module(file)
            if module is not None:
                self._register_module_plugins(module)

    def load_plugins_from_package(self, package_name: str) -> None:
        import importlib
        import pkgutil

        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            self._register_module_plugins(package)
            return

        for info in pkgutil.walk_packages(
            package.__path__, prefix=package.__name__ + "."
        ):
            try:
                module = importlib.import_module(info.name)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to import plugin module %s: %s", info.name, exc)
                continue
            self._register_module_plugins(module)

    # ------------------------------ runtime build -----------------------------
    def build_runtime(self) -> "AgentRuntime":
        registries = SystemRegistries(
            resources=self.resource_registry,
            tools=self.tool_registry,
            plugins=self.plugin_registry,
        )
        return AgentRuntime(registries)

    # ------------------------------ internals --------------------------------
    def _import_module(self, file: Path) -> ModuleType | None:
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

    def _register_module_plugins(self, module: ModuleType) -> None:
        import inspect

        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            try:
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                ):
                    self.add_plugin(obj({}))
                elif callable(obj) and name.endswith("_plugin"):
                    self.plugin(obj)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to register plugin from %s.%s: %s",
                    module.__name__,
                    name,
                    exc,
                )
                continue
