from __future__ import annotations

"""Pipeline component: initializer."""

import tomllib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Type

from entity.config.environment import load_env
from entity.config.models import EntityConfig, asdict
from entity.core.plugin_utils import import_plugin_class
from entity.core.plugins import BasePlugin, ResourcePlugin, ToolPlugin
from entity.core.registries import PluginRegistry, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.utils.logging import configure_logging, get_logger
from entity.workflows.discovery import discover_workflows, register_module_workflows
from pipeline.config import ConfigLoader
from pipeline.utils import DependencyGraph, resolve_stages
from pipeline.reliability import CircuitBreaker
from pipeline.exceptions import CircuitBreakerTripped

from .stages import PipelineStage
from .workflow import Workflow

logger = get_logger(__name__)


class ClassRegistry:
    """Store plugin classes and configs before instantiation."""

    def __init__(self) -> None:
        self._classes: Dict[str, type[BasePlugin]] = {}
        self._configs: Dict[str, Dict] = {}
        self._order: List[str] = []

    def register_class(
        self, plugin_class: type[BasePlugin], config: Dict, name: str
    ) -> None:
        self._classes[name] = plugin_class
        self._configs[name] = config
        self._order.append(name)
        self._validate_stage_assignment(name, plugin_class, config)

    def has_plugin(self, name: str) -> bool:
        return name in self._classes

    def list_plugins(self) -> List[str]:
        return list(self._order)

    def all_plugin_classes(self) -> Iterable[Tuple[type[BasePlugin], Dict]]:
        for name in self._order:
            cls = self._classes[name]
            yield cls, self._configs[name]

    def resource_classes(self) -> Iterable[Tuple[type, Dict]]:
        for name in self._order:
            cls = self._classes[name]
            if issubclass(cls, ResourcePlugin):
                yield name, cls, self._configs[name]

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

    def non_resource_non_tool_classes(self) -> Iterable[Tuple[type[BasePlugin], Dict]]:
        for name in self._order:
            cls = self._classes[name]
            if not issubclass(cls, (ResourcePlugin, ToolPlugin)):
                yield cls, self._configs[name]

    def _type_default_stages(self, cls: type[BasePlugin]) -> List[PipelineStage]:
        """Return default stages for the given plugin class."""

        from entity.core.plugins.base import AdapterPlugin, PromptPlugin

        if issubclass(cls, ToolPlugin):
            return [PipelineStage.DO]
        if issubclass(cls, PromptPlugin):
            return [PipelineStage.THINK]
        if issubclass(cls, AdapterPlugin):
            return [PipelineStage.PARSE, PipelineStage.DELIVER]
        return []

    def _resolve_plugin_stages(
        self, cls: type[BasePlugin], config: Dict
    ) -> tuple[List[PipelineStage], bool]:
        """Determine final stages and whether they were explicit."""

        cfg_value = config.get("stages") or config.get("stage")

        return resolve_stages(
            cls.__name__,
            cfg_value=cfg_value,
            attr_stages=getattr(cls, "stages", []),
            explicit_attr=bool(getattr(cls, "stages", [])),
            type_defaults=self._type_default_stages(cls),
            ensure_stage=PipelineStage.ensure,
            logger=logger,
            error_type=SystemError,
        )

    def _validate_stage_assignment(
        self, name: str, cls: type[BasePlugin], config: Dict
    ) -> None:
        if issubclass(cls, (ResourcePlugin, ToolPlugin)):
            return

        stages, _ = self._resolve_plugin_stages(cls, config)
        invalid = [s for s in stages if not isinstance(s, PipelineStage)]
        if invalid:
            raise SystemError(f"Plugin '{name}' has invalid stage values: {invalid}")


@asynccontextmanager
async def initialization_cleanup_context(container: ResourceContainer):
    """Ensure resources shut down if initialization fails."""

    try:
        yield
    except Exception:
        await container.shutdown_all()
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

    def _type_default_stages(self, cls: type[BasePlugin]) -> List[PipelineStage]:
        """Return default stages for the given plugin class."""

        from entity.core.plugins.base import AdapterPlugin, PromptPlugin

        if issubclass(cls, ToolPlugin):
            return [PipelineStage.DO]
        if issubclass(cls, PromptPlugin):
            return [PipelineStage.THINK]
        if issubclass(cls, AdapterPlugin):
            return [PipelineStage.PARSE, PipelineStage.DELIVER]
        return []

    def _resolve_plugin_stages(
        self, cls: type[BasePlugin], instance: BasePlugin, config: Dict
    ) -> tuple[List[PipelineStage], bool]:
        """Determine final stages and whether they were explicit."""

        cfg_value = config.get("stages") or config.get("stage")

        return resolve_stages(
            cls.__name__,
            cfg_value=cfg_value,
            attr_stages=getattr(instance, "stages", []),
            explicit_attr=getattr(instance, "_explicit_stages", False),
            type_defaults=self._type_default_stages(cls),
            ensure_stage=PipelineStage.ensure,
            logger=logger,
            auto_inferred=getattr(instance, "_auto_inferred_stages", False),
            error_type=SystemError,
        )

    async def initialize(self):
        self._discover_plugins()
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
        for section in resource_sections:
            entries = self.config.get("plugins", {}).get(section, {})
            for name, config in entries.items():
                cls_path = config.get("type")
                if not cls_path:
                    raise ValueError(
                        f"Resource '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                registry.register_class(cls, config, name)
                dep_graph[name] = getattr(cls, "dependencies", [])

        for section in ["tools", "adapters", "prompts"]:
            for name, config in self.config.get("plugins", {}).get(section, {}).items():
                cls_path = config.get("type")
                if not cls_path:
                    raise ValueError(
                        f"{section[:-1].capitalize()} '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                registry.register_class(cls, config, name)
                dep_graph[name] = getattr(cls, "dependencies", [])

        # Validate workflow references
        for stage_plugins in workflow.stage_map.values():
            for plugin_name in stage_plugins:
                if not registry.has_plugin(plugin_name):
                    available = registry.list_plugins()
                    raise SystemError(
                        f"Workflow references unknown plugin '{plugin_name}'. Available: {available}"
                    )

        # Validate dependencies declared by each plugin class
        for plugin_class, _ in registry.all_plugin_classes():
            result = plugin_class.validate_dependencies(registry)
            if not result.success:
                raise SystemError(
                    f"Dependency validation failed for {plugin_class.__name__}:"
                    f"{result.error_message}"
                )

        # Phase 2: dependency validation
        self._validate_dependency_graph(registry, dep_graph)
        for plugin_class, config in registry.all_plugin_classes():
            result = plugin_class.validate_config(config)
            if not result.success:
                raise SystemError(
                    f"Config validation failed for {plugin_class.__name__}: {result.error_message}"
                )

        # Phase 3: initialize resources via container
        resource_container = self.resource_container_cls()
        for name, cls, config in registry.resource_classes():
            resource_container.register(name, cls, config)

        async with initialization_cleanup_context(resource_container):
            await resource_container.build_all()

            breaker_cfg = self.config.get("runtime_validation_breaker", {})
            breaker = CircuitBreaker(
                failure_threshold=breaker_cfg.get("failure_threshold", 3),
                recovery_timeout=breaker_cfg.get("recovery_timeout", 60.0),
            )
            for name, resource in resource_container._resources.items():
                validate = getattr(resource, "validate_runtime", None)
                if not callable(validate):
                    continue

                async def _run_validation() -> None:
                    result = await validate()
                    if not result.success:
                        raise RuntimeError(result.error_message)

                try:
                    await breaker.call(_run_validation)
                except CircuitBreakerTripped as exc:
                    raise SystemError(
                        "Runtime validation failure threshold exceeded"
                    ) from exc
                except Exception as exc:
                    logger.error("Runtime validation failed for %s: %s", name, exc)
                    if breaker._failure_count >= breaker.failure_threshold:
                        raise SystemError(
                            "Runtime validation failure threshold exceeded"
                        ) from exc

            # Phase 3.5: register tools
            tr_cfg = self.config.get("tool_registry", {})
            tool_registry = self.tool_registry_cls(
                concurrency_limit=tr_cfg.get("concurrency_limit", 5)
            )
            for name, cls, config in registry.named_tool_classes():
                instance = cls(config)
                await tool_registry.add(name, instance)

            # Phase 4: instantiate prompt and adapter plugins
            plugin_registry = self.plugin_registry_cls()
            for cls, config in registry.non_resource_non_tool_classes():
                instance = cls(config)
                stages, _ = self._resolve_plugin_stages(cls, instance, config)
                for stage in stages:
                    await plugin_registry.register_plugin_for_stage(
                        instance, PipelineStage.ensure(stage)
                    )

        return plugin_registry, resource_container, tool_registry, workflow

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
                    raise SystemError(
                        f"Plugin '{plugin_name}' requires '{dep_name}' but it's not registered. "
                        f"Available: {available}"
                    )
                if dep_name in graph_map:
                    graph_map[dep_name].append(plugin_name)

        # DependencyGraph may enforce valid dependencies but should not reorder
        # plugins. Execution strictly follows YAML order.
        DependencyGraph(graph_map).topological_sort()
