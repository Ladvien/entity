from __future__ import annotations

"""Pipeline component: agent."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, cast, Mapping, Iterable

from .builder import _AgentBuilder
from .exceptions import PipelineError
from .registries import PluginRegistry, SystemRegistries
from .runtime import _AgentRuntime
from pipeline.workflow import Pipeline, WorkflowMapping


@dataclass
class Agent:
    """High level agent wrapper combining builder and runtime."""

    config_path: str | None = None
    pipeline: Pipeline | None = None
    _builder: _AgentBuilder | None = field(default=None, init=False)
    _runtime: _AgentRuntime | None = field(default=None, init=False)
    _workflows: dict[str, type] = field(default_factory=dict, init=False)

    @property
    def builder(self) -> _AgentBuilder:
        """Lazily create and return an :class:`_AgentBuilder`."""

        if self._builder is None:
            self._builder = _AgentBuilder()
        return self._builder

    # ------------------------------------------------------------------
    # Delegated plugin helpers
    # ------------------------------------------------------------------
    def add_plugin(self, plugin: Any) -> None:  # pragma: no cover - delegation
        """Register a plugin on the underlying builder."""

        self.builder.add_plugin(plugin)

    def plugin(
        self,
        func: Optional[Callable[..., Any]] = None,
        **hints: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
        """Decorator for registering ``func`` as a plugin."""

        return self.builder.plugin(func, **hints)

    def load_plugins_from_directory(
        self, directory: str
    ) -> None:  # pragma: no cover - delegation
        """Load and register all plugins from ``directory``."""

        self.builder.load_plugins_from_directory(directory)

    def load_plugins_from_package(
        self, package_name: str
    ) -> None:  # pragma: no cover - delegation
        """Import a package and register any plugins it contains."""

        self.builder.load_plugins_from_package(package_name)

    # ------------------------------------------------------------------
    # Workflow helpers
    # ------------------------------------------------------------------
    @property
    def workflows(self) -> Dict[str, Type[Workflow]]:
        return self._workflows

    def load_workflows_from_directory(self, directory: str) -> None:
        self._workflows.update(discover_workflows(directory))

    def load_workflows_from_package(self, package_name: str) -> None:
        import importlib
        import pkgutil

        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            register_module_workflows(package, self._workflows)
            return

        for info in pkgutil.walk_packages(
            package.__path__, prefix=package.__name__ + "."
        ):
            try:
                module = importlib.import_module(info.name)
            except Exception:  # noqa: BLE001
                continue
            register_module_workflows(module, self._workflows)

    @classmethod
    def from_directory(
        cls, directory: str, *, workflow: Workflow | None = None
    ) -> "Agent":
        agent = cls(workflow=workflow)
        agent.load_plugins_from_directory(directory)
        return agent

    @classmethod
    def from_package(
        cls, package_name: str, *, workflow: Workflow | None = None
    ) -> "Agent":
        agent = cls(workflow=workflow)
        agent.load_plugins_from_package(package_name)
        return agent

    @classmethod
    def from_config(
        cls, cfg: str | Mapping[str, Any], *, env_file: str = ".env"
    ) -> "Agent":
        """Instantiate an agent from a YAML/JSON path or mapping."""

        from pathlib import Path
        import asyncio
        from pipeline.initializer import SystemInitializer

        if isinstance(cfg, Mapping):
            initializer = SystemInitializer.from_dict(cfg, env_file)
            path = None
        else:
            path = str(cfg)
            suffix = Path(path).suffix
            if suffix == ".json":
                initializer = SystemInitializer.from_json(path, env_file)
            else:
                initializer = SystemInitializer.from_yaml(path, env_file)

        async def _build() -> tuple[_AgentRuntime, dict[str, type]]:
            plugins, resources, tools, _ = await initializer.initialize()
            caps = SystemRegistries(resources=resources, tools=tools, plugins=plugins)
            return _AgentRuntime(caps), initializer.workflows

        runtime, workflows = asyncio.run(_build())
        agent = cls(config_path=path)
        agent._runtime = runtime
        agent._workflows = workflows
        return agent

    # ------------------------------------------------------------------
    async def _ensure_runtime(self) -> None:
        if self._runtime is None:
            self._runtime = self.builder.build_runtime()

    @property
    def runtime(self) -> _AgentRuntime:
        if self._runtime is None:
            raise PipelineError("Agent not initialized; call an async method")
        return self._runtime

    async def run_message(self, message: str) -> Dict[str, Any]:
        """Run ``message`` through the runtime pipeline and return results."""

        await self._ensure_runtime()
        if self._runtime is None:  # pragma: no cover - sanity check
            raise RuntimeError("Runtime not initialized")
        runtime = cast(_AgentRuntime, self._runtime)
        return cast(Dict[str, Any], await runtime.run_pipeline(message))

    async def handle(self, message: str) -> Dict[str, Any]:
        """Public alias for :meth:`run_message`."""

        return await self.run_message(message)

    def get_capabilities(self) -> SystemRegistries:
        if self._runtime is None:
            raise PipelineError("Agent not initialized")
        return self._runtime.capabilities

    # ------------------------------------------------------------------
    # Compatibility helpers
    # ------------------------------------------------------------------
    @property
    def plugin_registry(self) -> "PluginRegistry":  # pragma: no cover - passthrough
        if self._runtime is not None:
            return self._runtime.capabilities.plugins
        return self.builder.plugin_registry

    @property
    def plugins(self) -> "PluginRegistry":  # pragma: no cover - passthrough
        if self._runtime is not None:
            return self._runtime.capabilities.plugins
        return self.builder.plugin_registry
