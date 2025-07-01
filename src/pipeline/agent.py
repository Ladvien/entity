from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import logging
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Optional, cast

from registry import (PluginRegistry, ResourceRegistry, SystemRegistries,
                      ToolRegistry)

from .adapters.http import HTTPAdapter
from .adapters.websocket import WebSocketAdapter
from .pipeline import execute_pipeline
from .plugins import BasePlugin
from .plugins.classifier import PluginAutoClassifier

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """Minimal agent with plugin decorator and pipeline execution."""

    plugin_registry: PluginRegistry = field(default_factory=PluginRegistry)
    resource_registry: ResourceRegistry = field(default_factory=ResourceRegistry)
    tool_registry: ToolRegistry = field(default_factory=ToolRegistry)

    # Backwards compatibility aliases
    @property
    def plugins(self) -> PluginRegistry:
        return self.plugin_registry

    @property
    def resources(self) -> ResourceRegistry:
        return self.resource_registry

    @property
    def tools(self) -> ToolRegistry:
        return self.tool_registry

    def add_plugin(self, plugin: Any) -> None:
        """Register a plugin instance for its stages."""
        if not inspect.iscoroutinefunction(getattr(plugin, "_execute_impl", None)):
            name = getattr(plugin, "name", plugin.__class__.__name__)
            raise TypeError(f"Plugin '{name}' must implement async '_execute_impl'")
        for stage in getattr(plugin, "stages", []):
            name = getattr(plugin, "name", plugin.__class__.__name__)
            self.plugin_registry.register_plugin_for_stage(plugin, stage, name)

    def plugin(self, func: Optional[Callable] = None, **hints):
        """Decorator to register a function as a plugin."""

        def decorator(f: Callable) -> Callable:
            plugin = PluginAutoClassifier.classify(f, hints)
            self.add_plugin(plugin)
            return f

        return decorator(func) if func else decorator

    # ------------------------------------------------------------------
    # Plugin loading utilities
    # ------------------------------------------------------------------

    @classmethod
    def from_directory(cls, directory: str) -> "Agent":
        """Create an agent and load plugins from ``directory``.

        Plugin modules that fail to import are logged and ignored.
        """

        agent = cls()
        agent.load_plugins_from_directory(directory)
        return agent

    @classmethod
    def from_package(cls, package_name: str) -> "Agent":
        """Create an agent and load plugins from ``package_name``.

        All modules within the package are imported and scanned for plugin
        objects. Modules that fail to import are logged and skipped.
        """

        agent = cls()
        agent.load_plugins_from_package(package_name)
        return agent

    def load_plugins_from_directory(self, directory: str) -> None:
        """Load plugin modules from ``directory``."""

        for file in Path(directory).glob("*.py"):
            if file.name.startswith("_"):
                continue
            module = self._import_module(file)
            if module is not None:
                self._register_module_plugins(module)

    def load_plugins_from_package(self, package_name: str) -> None:
        """Load plugin modules from a package and its submodules."""

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

    def _import_module(self, file: Path) -> ModuleType | None:
        """Import ``file`` and return the loaded module or ``None`` on error."""

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
        """Register plugins defined in ``module``."""

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
                    "Failed to register plugin %s from %s: %s",
                    name,
                    getattr(module, "__file__", "<unknown>"),
                    exc,
                )

    def create_http_adapter(
        self, host: str = "127.0.0.1", port: int = 8000
    ) -> HTTPAdapter:
        """Return an :class:`HTTPAdapter` for this agent's registries."""

        config: dict[str, Any] = {"host": host, "port": port}
        return HTTPAdapter(config=config)

    def create_websocket_adapter(
        self, host: str = "127.0.0.1", port: int = 8001
    ) -> WebSocketAdapter:
        """Return a :class:`WebSocketAdapter` for this agent's registries."""

        config: dict[str, Any] = {"host": host, "port": port}
        return WebSocketAdapter(config=config)

    async def serve_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Serve requests using the :class:`HTTPAdapter`."""

        adapter = self.create_http_adapter(host, port)
        registries = SystemRegistries(
            resources=self.resource_registry,
            tools=self.tool_registry,
            plugins=self.plugin_registry,
        )
        await adapter.serve(registries)

    async def serve_websocket(self, host: str = "127.0.0.1", port: int = 8001) -> None:
        """Serve requests using the :class:`WebSocketAdapter`."""

        adapter = self.create_websocket_adapter(host, port)
        registries = SystemRegistries(
            resources=self.resource_registry,
            tools=self.tool_registry,
            plugins=self.plugin_registry,
        )
        await adapter.serve(registries)

    def run_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Convenience wrapper to start the HTTP adapter."""

        asyncio.run(self.serve_http(host, port))

    def run_websocket(self, host: str = "127.0.0.1", port: int = 8001) -> None:
        """Convenience wrapper to start the WebSocket adapter."""

        asyncio.run(self.serve_websocket(host, port))

    async def run_message(self, message: str) -> Dict[str, Any]:
        registries = SystemRegistries(
            resources=self.resource_registry,
            tools=self.tool_registry,
            plugins=self.plugin_registry,
        )
        return cast(Dict[str, Any], await execute_pipeline(message, registries))

    async def handle(self, message: str) -> Dict[str, Any]:
        """Backward-compatible wrapper around :meth:`run_message`."""
        return await self.run_message(message)
