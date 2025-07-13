"""Pipeline component: initializer."""

from __future__ import annotations

import tomllib
from contextlib import asynccontextmanager
import asyncio
import inspect
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Type

from entity.config.environment import load_env
from entity.config.models import EntityConfig, PluginConfig, asdict
from entity.core.plugin_utils import import_plugin_class
from entity.core.plugins import Plugin, ResourcePlugin, ToolPlugin
from entity.core.registry_validator import RegistryValidator
from entity.core.registries import PluginRegistry, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.utils.logging import configure_logging, get_logger
from entity.workflows.discovery import discover_workflows, register_module_workflows
from .config import ConfigLoader
from .utils import DependencyGraph, resolve_stages, StageResolver
from entity.core.circuit_breaker import CircuitBreaker, BreakerManager
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

    @staticmethod
    def _validate_plugin_type(name: str, cls: type[Plugin], section: str) -> None:
        from entity.core.registry_validator import RegistryValidator

        RegistryValidator._validate_plugin_type(name, cls, section)

    def register_class(
        self,
        plugin_class: type[Plugin],
        config: Dict,
        name: str,
        layer: int,
        section: str,
    ) -> None:
        self._classes[name] = plugin_class
        self._configs[name] = config
        self._layers[name] = layer
        self._order.append(name)
        self._validate_plugin_type(name, plugin_class, section)
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
        from entity.core.plugins import (
            AdapterPlugin,
            InputAdapterPlugin,
            OutputAdapterPlugin,
            InfrastructurePlugin,
        )

        if issubclass(cls, ResourcePlugin):
            if (
                config.get("stage")
                or config.get("stages")
                or getattr(cls, "stages", None)
            ):
                raise InitializationError(
                    name,
                    "stage validation",
                    "Resource plugins cannot define pipeline stages.",
                )
            return
        if issubclass(cls, InfrastructurePlugin):
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

        if issubclass(cls, ToolPlugin) and any(s != PipelineStage.DO for s in stages):
            raise InitializationError(
                name,
                "stage validation",
                "ToolPlugin must use DO stage",
            )

        if any(s == PipelineStage.INPUT for s in stages) and not issubclass(
            cls, InputAdapterPlugin
        ):
            raise InitializationError(
                name,
                "stage validation",
                "Only InputAdapterPlugin can register for INPUT stage",
            )
        if any(s == PipelineStage.OUTPUT for s in stages) and not issubclass(
            cls, OutputAdapterPlugin
        ):
            raise InitializationError(
                name,
                "stage validation",
                "Only OutputAdapterPlugin can register for OUTPUT stage",
            )

        if issubclass(cls, InputAdapterPlugin) and any(
            s != PipelineStage.INPUT for s in stages
        ):
            raise InitializationError(
                name,
                "stage validation",
                "InputAdapterPlugin must use INPUT stage",
            )
        if issubclass(cls, OutputAdapterPlugin) and any(
            s != PipelineStage.OUTPUT for s in stages
        ):
            raise InitializationError(
                name,
                "stage validation",
                "OutputAdapterPlugin must use OUTPUT stage",
            )
        if issubclass(cls, AdapterPlugin) and any(
            s not in {PipelineStage.INPUT, PipelineStage.OUTPUT} for s in stages
        ):
            raise InitializationError(
                name,
                "stage validation",
                "AdapterPlugin stages must be INPUT and/or OUTPUT",
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
        strict_stages: bool = False,
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

        infrastructure = self._config_model.plugins.infrastructure
        if "database_backend" not in infrastructure:
            infrastructure["database_backend"] = PluginConfig(
                type="entity.infrastructure.duckdb:DuckDBInfrastructure"
            )
            self.config.setdefault("plugins", {}).setdefault("infrastructure", {})[
                "database_backend"
            ] = {"type": "entity.infrastructure.duckdb:DuckDBInfrastructure"}
        resources = self._config_model.plugins.resources
        if "database" not in resources:
            resources["database"] = PluginConfig(
                type="entity.resources.interfaces.duckdb_resource:DuckDBResource"
            )
            self.config.setdefault("plugins", {}).setdefault("resources", {})[
                "database"
            ] = {"type": "entity.resources.interfaces.duckdb_resource:DuckDBResource"}
        if "logging" not in resources:
            resources["logging"] = PluginConfig(
                type="entity.resources.logging:LoggingResource"
            )
            self.config.setdefault("plugins", {}).setdefault("resources", {})[
                "logging"
            ] = {"type": "entity.resources.logging:LoggingResource"}

        self.plugin_registry_cls = plugin_registry_cls
        self.tool_registry_cls = tool_registry_cls
        self.resource_container_cls = resource_container_cls
        self.strict_stages = strict_stages
        self.workflows: Dict[str, Type] = {}
        self._plugins: list[Plugin] = []
        self.plugin_registry: PluginRegistry | None = None
        self.resource_container: ResourceContainer | None = None
        self.tool_registry: ToolRegistry | None = None

    def _ensure_metrics_collector_config(self) -> None:
        """Warn when metrics collection is disabled."""

        resources_cfg = self.config.get("plugins", {}).get("resources", {})
        if "metrics_collector" not in resources_cfg:
            logger.warning(
                "MetricsCollectorResource not configured; metrics will not be recorded"
            )

    def _assign_shared_resources(
        self, instance: Any, resource_container: "ResourceContainer"
    ) -> None:
        """Attach metrics and logging resources to ``instance`` if available."""

        metrics = resource_container.get("metrics_collector")
        if metrics is not None:
            setattr(instance, "metrics_collector", metrics)

        logger_res = resource_container.get("logging")
        if logger_res is not None:
            setattr(instance, "logging", logger_res)

    def _validate_plugin_attributes(
        self, name: str, cls: type[Plugin], section: str, cfg: Dict
    ) -> None:
        """Ensure discovered plugin defines required class attributes."""

        from entity.core.plugins import (
            AgentResource,
            InfrastructurePlugin,
            ResourcePlugin,
            PromptPlugin,
        )

        if issubclass(cls, PromptPlugin):
            if not (
                cfg.get("stage") or cfg.get("stages") or getattr(cls, "stages", None)
            ):
                raise InitializationError(
                    name,
                    "plugin discovery",
                    "Prompt plugins must define non-empty 'stages'",
                )

        if issubclass(cls, InfrastructurePlugin) and not getattr(
            cls, "infrastructure_type", ""
        ):
            raise InitializationError(
                name,
                "plugin discovery",
                "Infrastructure plugins must define infrastructure_type",
            )

        if issubclass(cls, ResourcePlugin) and not issubclass(cls, AgentResource):
            deps = getattr(cls, "infrastructure_dependencies", None)
            if not deps:
                raise InitializationError(
                    name,
                    "plugin discovery",
                    "Resource plugins must declare infrastructure_dependencies",
                )

    @classmethod
    def from_yaml(
        cls, yaml_path: str, env_file: str = ".env", *, strict_stages: bool = False
    ) -> "SystemInitializer":
        data = ConfigLoader.from_yaml(yaml_path, env_file)
        model = EntityConfig.from_dict(data)
        return cls(model, env_file, strict_stages=strict_stages)

    @classmethod
    def from_json(
        cls, json_path: str, env_file: str = ".env", *, strict_stages: bool = False
    ) -> "SystemInitializer":
        data = ConfigLoader.from_json(json_path, env_file)
        model = EntityConfig.from_dict(data)
        return cls(model, env_file, strict_stages=strict_stages)

    @classmethod
    def from_dict(
        cls, cfg: Dict[str, Any], env_file: str = ".env", *, strict_stages: bool = False
    ) -> "SystemInitializer":
        data = ConfigLoader.from_dict(cfg, env_file)
        model = EntityConfig.from_dict(data)
        return cls(model, env_file, strict_stages=strict_stages)

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
                        cls = import_plugin_class(cls_path)
                        try:
                            RegistryValidator._validate_plugin_type(name, cls, section)
                            RegistryValidator._validate_stage_assignment(
                                name, cls, meta
                            )
                            self._validate_plugin_attributes(name, cls, section, meta)
                        except SystemError as exc:
                            raise InitializationError(
                                name, "plugin discovery", str(exc)
                            ) from exc
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
        """Determine final stages and whether they were explicit.

        This mirrors :meth:`StageResolver._resolve_plugin_stages` but
        operates on an instantiated plugin. The returned ``explicit`` flag
        is ``True`` when stage information originates from configuration,
        the instance, or class attributes. If no stage is defined, the
        fallback ``THINK`` stage is considered explicit.
        """

        stages = resolve_stages(cls, config)
        explicit = bool(
            (config.get("stage") or config.get("stages"))
            or getattr(instance, "_explicit_stages", False)
            or getattr(cls, "stages", None)
            or getattr(cls, "stage", None)
        )
        if not explicit:
            explicit = True
        return stages, explicit

    def _warn_stage_mismatches(self, registry: ClassRegistry) -> None:
        """Log a warning when config stages override class stages."""

        for cls, config in registry.all_plugin_classes():
            cfg_value = config.get("stages") or config.get("stage")
            class_value = getattr(cls, "stages", None) or getattr(cls, "stage", None)
            if cfg_value is None or class_value is None:
                continue

            cfg_stages = resolve_stages(cls, config)
            class_stages = (
                class_value if isinstance(class_value, list) else [class_value]
            )
            class_stages = [PipelineStage.ensure(s) for s in class_stages]
            if cfg_stages != class_stages:
                msg = (
                    f"{cls.__name__} configured stages {cfg_stages} "
                    f"override class stages {class_stages}"
                )
                if self.strict_stages:
                    raise InitializationError(cls.__name__, "stage validation", msg)
                logger.warning(msg)

    def _register_plugins(
        self, registry: ClassRegistry, dep_graph: Dict[str, List[str]]
    ) -> None:
        """Register plugin classes and enforce default dependencies."""

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

        plugins_cfg = self.config.get("plugins", {})
        add_metrics = "metrics_collector" in plugins_cfg.get("resources", {})

        for section in resource_sections:
            entries = plugins_cfg.get(section, {})
            layer = layer_map[section]
            for name, config in entries.items():
                cls_path = config.get("type")
                if not cls_path:
                    raise ValueError(
                        f"Resource '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                deps = list(getattr(cls, "dependencies", []))
                if not add_metrics and "metrics_collector" in deps:
                    deps.remove("metrics_collector")
                if "logging" not in deps and cls.__name__ != "LoggingResource":
                    deps.append("logging")
                from entity.core.plugins import InfrastructurePlugin

                if issubclass(cls, InfrastructurePlugin):
                    deps = [
                        d for d in deps if d not in {"logging", "metrics_collector"}
                    ]
                if add_metrics and (
                    cls.__name__ != "MetricsCollectorResource"
                    and "metrics_collector" not in deps
                ):
                    deps.append("metrics_collector")
                cls.dependencies = deps
                registry.register_class(cls, config, name, layer, section)
                dep_graph[name] = deps

        for section in ["tools", "adapters", "prompts"]:
            entries = self.config.get("plugins", {}).get(section, {})
            for name, config in entries.items():
                cls_path = config.get("type")
                if not cls_path:
                    raise ValueError(
                        f"{section[:-1].capitalize()} '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                deps = list(getattr(cls, "dependencies", []))
                if not add_metrics and "metrics_collector" in deps:
                    deps.remove("metrics_collector")
                if "logging" not in deps and cls.__name__ != "LoggingResource":
                    deps.append("logging")
                if add_metrics and (
                    cls.__name__ != "MetricsCollectorResource"
                    and "metrics_collector" not in deps
                ):
                    deps.append("metrics_collector")
                cls.dependencies = deps
                registry.register_class(cls, config, name, 4, section)
                dep_graph[name] = deps

    async def initialize(self):
        self._discover_plugins()
        self._ensure_metrics_collector_config()
        self._discover_workflows()

        registry = ClassRegistry()
        dep_graph: Dict[str, List[str]] = {}
        wf_cfg = {}
        if self._config_model.workflow is not None:
            wf_cfg = self._config_model.workflow.stages
        workflow = Workflow.from_dict(wf_cfg)

        # Phase 1: register all plugin classes
        self._register_plugins(registry, dep_graph)

        self._warn_stage_mismatches(registry)

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

        # Phase 1: syntax validation
        for plugin_class, config in registry.all_plugin_classes():
            user_cfg = {
                k: v
                for k, v in config.items()
                if k not in {"type", "dependencies", "stage", "stages"}
            }
            result = await plugin_class.validate_config(user_cfg)
            if not result.success:
                raise InitializationError(
                    plugin_class.__name__,
                    "syntax validation",
                    f"{result.message}. Update the plugin configuration.",
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
        for plugin_class, _ in registry.all_plugin_classes():
            result = await plugin_class.validate_dependencies(registry)
            if not result.success:
                raise InitializationError(
                    plugin_class.__name__,
                    "dependency validation",
                    f"{result.message}. Fix plugin dependencies.",
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

            breaker_mgr = BreakerManager.from_config(cfg, settings)

            tasks: list[asyncio.Task] = []
            resources: list[tuple[str, CircuitBreaker]] = []

            for name, resource in resource_container._resources.items():
                validate = getattr(resource, "validate_runtime", None)
                if not callable(validate):
                    continue

                category = getattr(resource, "resource_category", None)
                if not category:
                    category = getattr(resource, "infrastructure_type", "").lower()

                breaker = breaker_mgr.get(category)

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
                self._assign_shared_resources(instance, resource_container)
                await tool_registry.add(name, instance)

            # Phase 4: instantiate prompt and adapter plugins
            plugin_registry = self.plugin_registry_cls()
            self.plugin_registry = plugin_registry
            for cls, config in registry.non_resource_non_tool_classes():
                instance = cls(config)
                self._assign_shared_resources(instance, resource_container)
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
                            f"Missing dependency '{dep_name}'. "
                            "Ensure it is registered and declared correctly."
                        ),
                    )
                dep_cls = registry._classes.get(dep_name)
                from entity.core.plugins import ResourcePlugin

                if dep_cls is not None and not issubclass(dep_cls, ResourcePlugin):
                    raise InitializationError(
                        plugin_name,
                        "dependency graph validation",
                        f"Dependency '{dep_name}' is not a resource plugin.",
                    )
                if dep_name in graph_map:
                    graph_map[dep_name].append(plugin_name)

        # DependencyGraph may enforce valid dependencies but should not reorder
        # plugins. Execution strictly follows YAML order.
        DependencyGraph(graph_map).topological_sort()

    def _ensure_canonical_resources(self, container: ResourceContainer) -> None:
        """Verify required canonical resources are registered."""

        registered = set(container._classes)

        # Ensure logging is available for dependency checks
        if "logging" not in registered:
            from entity.resources.logging import LoggingResource

            container.register("logging", LoggingResource, {}, layer=3)
            registered.add("logging")

        if "database_backend" not in registered:
            from entity.infrastructure.duckdb import DuckDBInfrastructure

            container.register("database_backend", DuckDBInfrastructure, {}, layer=1)
            registered.add("database_backend")

        if "database" not in registered:
            from entity.resources.interfaces.duckdb_resource import DuckDBResource

            container.register("database", DuckDBResource, {}, layer=2)
            registered.add("database")

        if "vector_store" not in registered:
            from entity.resources.interfaces.duckdb_vector_store import (
                DuckDBVectorStore,
            )

            container.register("vector_store", DuckDBVectorStore, {}, layer=2)
            registered.add("vector_store")

        required = {"memory", "llm", "storage"}
        missing = required - set(container._classes)
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise InitializationError(
                "canonical resources",
                "pre-flight check",
                f"Missing canonical resources: {missing_list}. Add them to your configuration.",
                kind="Resource",
            )


def validate_reconfiguration_params(
    old_config: Dict[str, Any], new_config: Dict[str, Any]
) -> "ValidationResult":
    """Ensure only configuration values are changed on reload."""

    from entity.core.plugins import ValidationResult

    for key in ("type", "stage", "stages", "dependencies"):
        if key in new_config and new_config.get(key) != old_config.get(key):
            return ValidationResult.error_result("Topology changes require restart")

    return ValidationResult.success_result()
