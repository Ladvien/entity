"""Pipeline component: initializer."""

from __future__ import annotations

import tomllib
from contextlib import asynccontextmanager
import asyncio
import inspect
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Type

from entity.config.environment import load_env
from entity.config.models import EntityConfig, asdict
from entity.core.plugin_utils import import_plugin_class
from entity.core.plugins import Plugin, ResourcePlugin, ToolPlugin
from entity.core.registries import PluginRegistry, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.utils.logging import configure_logging, get_logger
from entity.workflows.discovery import discover_workflows, register_module_workflows
from .config import ConfigLoader
from .utils import DependencyGraph, resolve_stages, StageResolver
from .reliability import CircuitBreaker
from .exceptions import CircuitBreakerTripped
from .errors import InitializationError

from .stages import PipelineStage
from .workflow import Workflow

logger = get_logger(__name__)


class ClassRegistry(StageResolver):
    """Store plugin classes and configs before instantiation."""

    def __init__(self) -> None:
        self._classes: Dict[str, type[Plugin]] = {}
        self._configs: Dict[str, Dict] = {}
        self._layers: Dict[str, int] = {}
        self._order: List[str] = []

    def register_class(
        self, plugin_class: type[Plugin], config: Dict, name: str, layer: int
    ) -> None:
        self._classes[name] = plugin_class
        self._configs[name] = config
        self._layers[name] = layer
        self._order.append(name)
        self._validate_stage_assignment(name, plugin_class, config)

    def has_plugin(self, name: str) -> bool:
        return name in self._classes

    def list_plugins(self) -> List[str]:
        return list(self._order)

    def all_plugin_classes(self) -> Iterable[Tuple[type[Plugin], Dict]]:
        for name in self._order:
            cls = self._classes[name]
            yield cls, self._configs[name]

    def resource_classes(self) -> Iterable[Tuple[str, type, Dict, int]]:
        for name in self._order:
            cls = self._classes[name]
            if issubclass(cls, ResourcePlugin):
                layer = self._layers.get(name, 1)
                yield name, cls, self._configs[name], layer

    def tool_classes(self) -> Iterable[Tuple[type[ToolPlugin], Dict]]:
        for name in self._order:
            cls = self._classes[name]
            if issubclass(cls, ToolPlugin):
                yield cls, self._configs[name]

    def named_tool_classes(self) -> Iterable[Tuple[str, type[ToolPlugin], Dict]]:
        """Return registered tool plugin classes with their names."""

        for name in self._order:
            cls = self._classes[name]
            if issubclass(cls, ToolPlugin):
                yield name, cls, self._configs[name]

    def non_resource_non_tool_classes(self) -> Iterable[Tuple[type[Plugin], Dict]]:
        for name in self._order:
            cls = self._classes[name]
            if not issubclass(cls, (ResourcePlugin, ToolPlugin)):
                yield cls, self._configs[name]

    def _resolve_plugin_stages(
        self, cls: type[Plugin], config: Dict
    ) -> tuple[List[PipelineStage], bool]:
        """Determine final stages and whether they were explicit."""

        stages = resolve_stages(cls, config)
        explicit = bool(
            (config.get("stage") or config.get("stages"))
            or getattr(cls, "stages", None)
            or getattr(cls, "stage", None)
        )
        return stages, explicit

    def _validate_stage_assignment(
        self, name: str, cls: type[Plugin], config: Dict
    ) -> None:
        if issubclass(cls, (ResourcePlugin, ToolPlugin)):
            return

        stages, explicit = StageResolver._resolve_plugin_stages(
            cls, config, logger=logger
        )
        if not explicit:
            raise InitializationError(
                name,
                "stage validation",
                "Specify 'stage' or 'stages' on the plugin or in its configuration.",
            )
        invalid = [s for s in stages if not isinstance(s, PipelineStage)]
        if invalid:
            raise InitializationError(
                name,
                "stage validation",
                f"Invalid stage values: {invalid}. Use PipelineStage members.",
            )


@asynccontextmanager
async def initialization_cleanup_context(container: ResourceContainer):
    """Ensure resources shut down if initialization fails."""

    try:
        yield
    except Exception:
        await container.shutdown_all()
        raise


@asynccontextmanager
async def plugin_cleanup_context(plugins: list[Plugin]):
    """Shutdown plugins if initialization fails."""

    try:
        yield
    except Exception:
        for plugin in reversed(plugins):
            shutdown = getattr(plugin, "shutdown", None)
            if callable(shutdown):
                await shutdown()
        raise


class SystemInitializer:
    """Initialize and validate all plugins for the pipeline."""

    def __init__(
        self,
        config: Dict | None = None,
        env_file: str = ".env",
        *,
        plugin_registry_cls: Type[PluginRegistry] = PluginRegistry,
        tool_registry_cls: Type[ToolRegistry] = ToolRegistry,
        resource_container_cls: Type[ResourceContainer] = ResourceContainer,
    ) -> None:
        load_env(env_file)
        configure_logging()
        if isinstance(config, EntityConfig):
            self._config_model = config
            self.config = asdict(config)
        else:
            cfg = config or {}
            self._config_model = EntityConfig.from_dict(cfg)
            self.config = asdict(self._config_model)
        self.plugin_registry_cls = plugin_registry_cls
        self.tool_registry_cls = tool_registry_cls
        self.resource_container_cls = resource_container_cls
        self.workflows: Dict[str, Type] = {}
        self._plugins: list[Plugin] = []
        self.plugin_registry: PluginRegistry | None = None
        self.resource_container: ResourceContainer | None = None
        self.tool_registry: ToolRegistry | None = None

    def _ensure_metrics_collector_config(self) -> None:
        plugins_cfg = self.config.setdefault("plugins", {})
        resources_cfg = plugins_cfg.setdefault("resources", {})
        resources_cfg.setdefault(
            "metrics_collector",
            {"type": "entity.resources.metrics_collector:MetricsCollectorResource"},
        )

    @classmethod
    def from_yaml(cls, yaml_path: str, env_file: str = ".env") -> "SystemInitializer":
        data = ConfigLoader.from_yaml(yaml_path, env_file)
        model = EntityConfig.from_dict(data)
        return cls(model, env_file)

    @classmethod
    def from_json(cls, json_path: str, env_file: str = ".env") -> "SystemInitializer":
        data = ConfigLoader.from_json(json_path, env_file)
        model = EntityConfig.from_dict(data)
        return cls(model, env_file)

    @classmethod
    def from_dict(
        cls, cfg: Dict[str, Any], env_file: str = ".env"
    ) -> "SystemInitializer":
        data = ConfigLoader.from_dict(cfg, env_file)
        model = EntityConfig.from_dict(data)
        return cls(model, env_file)

    # --------------------------- plugin discovery ---------------------------
    def _discover_plugins(self) -> None:
        """Update configuration with plugins found in ``plugin_dirs``."""

        plugin_dirs = self.config.get("plugin_dirs", [])
        for directory in plugin_dirs:
            for pyproject in Path(directory).rglob("pyproject.toml"):
                try:
                    with open(pyproject, "rb") as fh:
                        data = tomllib.load(fh)
                except (FileNotFoundError, tomllib.TOMLDecodeError):
                    continue

                tool_section = data.get("tool", {})
                entity = tool_section.get("entity", {})
                plugins = entity.get("plugins", {})
                for section in [
                    "infrastructure",
                    "resources",
                    "agent_resources",
                    "custom_resources",
                    "tools",
                    "adapters",
                    "prompts",
                ]:
                    entries = plugins.get(section, {})
                    if not isinstance(entries, dict):
                        continue
                    cfg_section = self.config.setdefault("plugins", {}).setdefault(
                        section, {}
                    )
                    for name, meta in entries.items():
                        if name in cfg_section:
                            continue
                        if isinstance(meta, str):
                            cfg_section[name] = {"type": meta}
                            continue
                        if not isinstance(meta, dict):
                            continue
                        cls_path = meta.get("class") or meta.get("type")
                        if not cls_path:
                            continue
                        cfg = {"type": cls_path}
                        deps = meta.get("dependencies")
                        if deps:
                            cfg["dependencies"] = list(deps)
                        for k, v in meta.items():
                            if k not in {"class", "type", "dependencies"}:
                                cfg[k] = v
                        cfg_section[name] = cfg

    def _discover_workflows(self) -> None:
        """Load workflow classes from ``workflow_dirs`` into ``self.workflows``."""

        dirs = self.config.get("workflow_dirs", [])
        for directory in dirs:
            self.workflows.update(discover_workflows(directory))

    def get_resource_config(self, name: str) -> Dict:
        plugins = self.config.get("plugins", {})
        for section in (
            "agent_resources",
            "custom_resources",
            "resources",
            "infrastructure",
        ):
            cfg = plugins.get(section, {})
            if name in cfg:
                return cfg[name]
        raise KeyError(name)

    def get_tool_config(self, name: str) -> Dict:
        return self.config["plugins"]["tools"][name]

    def get_adapter_config(self, name: str) -> Dict:
        return self.config["plugins"]["adapters"][name]

    def get_prompt_config(self, name: str) -> Dict:
        return self.config["plugins"]["prompts"][name]

    # --------------------------- workflow discovery ---------------------------
    def load_workflows_from_directory(self, directory: str) -> None:
        """Load workflows from ``directory`` and store them."""

        self.workflows.update(discover_workflows(directory))

    def load_workflows_from_package(self, package_name: str) -> None:
        import importlib
        import pkgutil

        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            register_module_workflows(package, self.workflows)
            return

        for info in pkgutil.walk_packages(
            package.__path__, prefix=package.__name__ + "."
        ):
            try:
                module = importlib.import_module(info.name)
            except Exception:  # noqa: BLE001
                continue
            register_module_workflows(module, self.workflows)

    def _resolve_plugin_stages(
        self, cls: type[Plugin], instance: Plugin, config: Dict
    ) -> tuple[List[PipelineStage], bool]:
        """Determine final stages and whether they were explicit."""

        stages = resolve_stages(cls, config)
        explicit = bool(
            (config.get("stage") or config.get("stages"))
            or getattr(instance, "_explicit_stages", False)
            or getattr(cls, "stages", None)
            or getattr(cls, "stage", None)
        )
        return stages, explicit

    async def initialize(self):
        self._discover_plugins()
        self._ensure_metrics_collector_config()
        self._discover_workflows()

        registry = ClassRegistry()
        dep_graph: Dict[str, List[str]] = {}
        workflow = Workflow.from_dict(self.config.get("workflow"))

        # Phase 1: register all plugin classes
        resource_sections = [
            "infrastructure",
            "resources",
            "agent_resources",
            "custom_resources",
        ]
        layer_map = {
            "infrastructure": 1,
            "resources": 2,
            "agent_resources": 3,
            "custom_resources": 4,
        }
        for section in resource_sections:
            entries = self.config.get("plugins", {}).get(section, {})
            layer = layer_map[section]
            for name, config in entries.items():
                cls_path = config.get("type")
                if not cls_path:
                    raise ValueError(
                        f"Resource '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                deps = list(getattr(cls, "dependencies", []))
                if "metrics_collector" not in deps:
                    deps.append("metrics_collector")
                cls.dependencies = deps
                registry.register_class(cls, config, name, layer)
                dep_graph[name] = deps

        for section in ["tools", "adapters", "prompts"]:
            for name, config in self.config.get("plugins", {}).get(section, {}).items():
                cls_path = config.get("type")
                if not cls_path:
                    raise ValueError(
                        f"{section[:-1].capitalize()} '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                deps = list(getattr(cls, "dependencies", []))
                if "metrics_collector" not in deps:
                    deps.append("metrics_collector")
                cls.dependencies = deps
                registry.register_class(cls, config, name, 4)
                dep_graph[name] = deps

        # Validate workflow references
        for stage_plugins in workflow.stage_map.values():
            for plugin_name in stage_plugins:
                if not registry.has_plugin(plugin_name):
                    available = registry.list_plugins()
                    raise InitializationError(
                        plugin_name,
                        "workflow validation",
                        f"Unknown plugin referenced. Available plugins: {available}",
                    )

        # Validate dependencies declared by each plugin class
        for plugin_class, _ in registry.all_plugin_classes():
            result = await plugin_class.validate_dependencies(registry)
            if not result.success:
                raise InitializationError(
                    plugin_class.__name__,
                    "dependency validation",
                    f"{result.message}. Fix plugin dependencies.",
                )

        # Register resources early so we can verify canonical ones exist
        resource_container = self.resource_container_cls()
        self.resource_container = resource_container
        for name, cls, config, _layer in registry.resource_classes():
            resource_container.register(name, cls, config)

        # Ensure required canonical resources before dependency validation
        self._ensure_canonical_resources(resource_container)

        # Phase 2: dependency validation
        self._validate_dependency_graph(registry, dep_graph)
        for plugin_class, config in registry.all_plugin_classes():
            result = await plugin_class.validate_config(config)
            if not result.success:
                raise InitializationError(
                    plugin_class.__name__,
                    "config validation",
                    f"{result.message}. Update the plugin configuration.",
                )

        # Fail fast if any canonical resources are missing before initialization
        self._ensure_canonical_resources(resource_container)

        # Phase 3: initialize resources via container

        async with (
            initialization_cleanup_context(resource_container),
            plugin_cleanup_context(self._plugins),
        ):
            await resource_container.build_all()

            model = self._config_model
            cfg = model.runtime_validation_breaker
            settings = model.breaker_settings

            breaker_map = {
                "database": CircuitBreaker(
                    failure_threshold=cfg.database
                    or settings.database.failure_threshold,
                    recovery_timeout=cfg.recovery_timeout,
                ),
                "api": CircuitBreaker(
                    failure_threshold=cfg.api
                    or settings.external_api.failure_threshold,
                    recovery_timeout=cfg.recovery_timeout,
                ),
                "filesystem": CircuitBreaker(
                    failure_threshold=cfg.filesystem
                    or settings.file_system.failure_threshold,
                    recovery_timeout=cfg.recovery_timeout,
                ),
            }

            default_breaker = CircuitBreaker(
                failure_threshold=cfg.failure_threshold,
                recovery_timeout=cfg.recovery_timeout,
            )

            tasks: list[asyncio.Task] = []
            resources: list[tuple[str, CircuitBreaker]] = []

            for name, resource in resource_container._resources.items():
                validate = getattr(resource, "validate_runtime", None)
                if not callable(validate):
                    continue

                category = getattr(resource, "resource_category", None)
                if not category:
                    category = getattr(resource, "infrastructure_type", "").lower()

                breaker = breaker_map.get(category, default_breaker)

                async def _call_validation(
                    validate=validate,
                    breaker=breaker,
                ) -> None:
                    async def _run() -> None:
                        if len(inspect.signature(validate).parameters) == 1:
                            result = await validate(breaker)
                        else:
                            result = await validate()
                        if not result.success:
                            raise RuntimeError(result.message)

                    await breaker.call(_run)

                tasks.append(asyncio.create_task(_call_validation()))
                resources.append((name, breaker))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (name, breaker), result in zip(resources, results):
                if isinstance(result, Exception):
                    logger.error("Runtime validation failed for %s: %s", name, result)
                    if (
                        isinstance(result, CircuitBreakerTripped)
                        or breaker._failure_count >= breaker.failure_threshold
                    ):
                        raise InitializationError(
                            name,
                            "runtime validation",
                            "Failure threshold exceeded. Inspect resource configuration.",
                            kind="Resource",
                        ) from result
                else:
                    logger.info("Runtime validation succeeded for %s", name)

            # Phase 3.5: register tools
            tr_cfg = self.config.get("tool_registry", {})
            tool_registry = self.tool_registry_cls(
                concurrency_limit=tr_cfg.get("concurrency_limit", 5)
            )
            self.tool_registry = tool_registry
            for name, cls, config in registry.named_tool_classes():
                instance = cls(config)
                await tool_registry.add(name, instance)

            # Phase 4: instantiate prompt and adapter plugins
            plugin_registry = self.plugin_registry_cls()
            self.plugin_registry = plugin_registry
            for cls, config in registry.non_resource_non_tool_classes():
                instance = cls(config)
                stages, _ = StageResolver._resolve_plugin_stages(
                    cls, config, instance, logger=logger
                )
                for stage in stages:
                    await plugin_registry.register_plugin_for_stage(
                        instance, PipelineStage.ensure(stage)
                    )
                self._plugins.append(instance)

            for plugin in self._plugins:
                init = getattr(plugin, "initialize", None)
                if callable(init):
                    await init()

        return plugin_registry, resource_container, tool_registry, workflow

    async def shutdown(self) -> None:
        """Shutdown resources and plugins."""

        if self.resource_container is not None:
            await self.resource_container.shutdown_all()
        for plugin in reversed(self._plugins):
            shutdown = getattr(plugin, "shutdown", None)
            if callable(shutdown):
                await shutdown()

    def _validate_dependency_graph(
        self, registry: ClassRegistry, dep_graph: Dict[str, List[str]]
    ) -> None:
        graph_map: Dict[str, List[str]] = {name: [] for name in dep_graph}
        for plugin_name, deps in dep_graph.items():
            for dep in deps:
                optional = dep.endswith("?")
                dep_name = dep[:-1] if optional else dep
                if not registry.has_plugin(dep_name):
                    if optional:
                        continue
                    available = registry.list_plugins()
                    raise InitializationError(
                        plugin_name,
                        "dependency graph validation",
                        (
                            f"Missing dependency '{dep_name}'. Registered plugins: {available}."
                        ),
                    )
                if dep_name in graph_map:
                    graph_map[dep_name].append(plugin_name)

        # DependencyGraph may enforce valid dependencies but should not reorder
        # plugins. Execution strictly follows YAML order.
        DependencyGraph(graph_map).topological_sort()

    def _ensure_canonical_resources(self, container: ResourceContainer) -> None:
        """Verify required canonical resources are registered."""

        required = {"memory", "llm", "storage"}
        registered = set(container._classes)
        missing = required - registered
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise InitializationError(
                "canonical resources",
                "pre-flight check",
                f"Missing canonical resources: {missing_list}. Add them to your configuration.",
                kind="Resource",
            )

        if "logging" not in registered:
            from entity.resources.logging import LoggingResource

            container.register("logging", LoggingResource, {}, layer=3)
