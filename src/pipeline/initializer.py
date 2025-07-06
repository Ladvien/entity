from __future__ import annotations

import copy
import json
import tomllib
from contextlib import contextmanager
<<<<<<< HEAD
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
=======
from typing import Any, Dict, Iterable, List, Tuple, Type
>>>>>>> c72003e014c664863289e303211be6661160fdc6

from config.environment import load_env
from interfaces.plugins import import_plugin_class
from interfaces.resources import Resource
from pipeline.config.utils import interpolate_env_vars
from pipeline.resources.container import ResourceContainer
from pipeline.utils import DependencyGraph
from registry import PluginRegistry, ToolRegistry
from .stages import PipelineStage

from .base_plugins import BasePlugin, ResourcePlugin, ToolPlugin
from .defaults import DEFAULT_CONFIG
from .logging import configure_logging


class ClassRegistry:
    """Store plugin classes and configs before instantiation."""

    def __init__(self) -> None:
        self._classes: Dict[str, type[BasePlugin]] = {}
        self._configs: Dict[str, Dict] = {}

    def register_class(
        self, plugin_class: type[BasePlugin], config: Dict, name: str
    ) -> None:
        self._classes[name] = plugin_class
        self._configs[name] = config

    def has_plugin(self, name: str) -> bool:
        return name in self._classes

    def list_plugins(self) -> List[str]:
        return list(self._classes.keys())

    def all_plugin_classes(self) -> Iterable[Tuple[type[BasePlugin], Dict]]:
        for name, cls in self._classes.items():
            yield cls, self._configs[name]

    def resource_classes(self) -> Iterable[Tuple[type, Dict]]:
        for name, cls in self._classes.items():
            if issubclass(cls, ResourcePlugin) or issubclass(cls, Resource):
                yield cls, self._configs[name]

    def tool_classes(self) -> Iterable[Tuple[type[ToolPlugin], Dict]]:
        for name, cls in self._classes.items():
            if issubclass(cls, ToolPlugin):
                yield cls, self._configs[name]

    def non_resource_non_tool_classes(self) -> Iterable[Tuple[type[BasePlugin], Dict]]:
        for name, cls in self._classes.items():
            if (
                not issubclass(cls, ResourcePlugin)
                and not issubclass(cls, ToolPlugin)
                and not issubclass(cls, Resource)
            ):
                yield cls, self._configs[name]


@contextmanager
def initialization_cleanup_context():
    try:
        yield
    finally:
        pass


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
        self.config = config or copy.deepcopy(DEFAULT_CONFIG)
        self.plugin_registry_cls = plugin_registry_cls
        self.tool_registry_cls = tool_registry_cls
        self.resource_container_cls = resource_container_cls

    @classmethod
    def from_yaml(cls, yaml_path: str, env_file: str = ".env") -> "SystemInitializer":
        import yaml

        with open(yaml_path, "r") as fh:
            content = fh.read()
        config = yaml.safe_load(content)
        load_env(env_file)
        config = interpolate_env_vars(config)
        return cls(config, env_file)

    @classmethod
    def from_json(cls, json_path: str, env_file: str = ".env") -> "SystemInitializer":
        with open(json_path, "r") as fh:
            content = fh.read()
        config = json.loads(content or "{}")
        load_env(env_file)
        config = interpolate_env_vars(config)
        return cls(config, env_file)

    @classmethod
    def from_dict(
        cls, cfg: Dict[str, Any], env_file: str = ".env"
    ) -> "SystemInitializer":
        load_env(env_file)
        config = interpolate_env_vars(dict(cfg))
        return cls(config, env_file)

    # --------------------------- plugin discovery ---------------------------
    def _discover_plugins(self) -> None:
        """Update configuration with plugins found in ``plugin_dirs``."""

        plugin_dirs = self.config.get("plugin_dirs", [])
        for directory in plugin_dirs:
            for pyproject in Path(directory).rglob("pyproject.toml"):
                try:
                    with open(pyproject, "rb") as fh:
                        data = tomllib.load(fh)
                except Exception:  # pragma: no cover - invalid files skipped
                    continue

                tool_section = data.get("tool", {})
                entity = tool_section.get("entity", {})
                plugins = entity.get("plugins", {})
                for section in ["resources", "tools", "adapters", "prompts"]:
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

    def get_resource_config(self, name: str) -> Dict:
        return self.config["plugins"]["resources"][name]

    def get_tool_config(self, name: str) -> Dict:
        return self.config["plugins"]["tools"][name]

    def get_adapter_config(self, name: str) -> Dict:
        return self.config["plugins"]["adapters"][name]

    def get_prompt_config(self, name: str) -> Dict:
        return self.config["plugins"]["prompts"][name]

    async def initialize(self):
        self._discover_plugins()

        registry = ClassRegistry()
        dep_graph: Dict[str, List[str]] = {}

        # Phase 1: register all plugin classes
        resources = self.config.get("plugins", {}).get("resources", {})
        for name, config in resources.items():
            default_cfg = DEFAULT_CONFIG["plugins"]["resources"].get(name, {})
            cls_path = config.get("type", default_cfg.get("type"))
            if not cls_path:
                raise ValueError(f"Resource '{name}' must specify a full class path")
            cls = import_plugin_class(cls_path)
            registry.register_class(cls, config, name)
            dep_graph[name] = getattr(cls, "dependencies", [])

        for section in ["tools", "adapters", "prompts"]:
            for name, config in self.config.get("plugins", {}).get(section, {}).items():
                default_cfg = DEFAULT_CONFIG["plugins"].get(section, {}).get(name, {})
                cls_path = config.get("type", default_cfg.get("type"))
                if not cls_path:
                    raise ValueError(
                        f"{section[:-1].capitalize()} '{name}' must specify a full class path"
                    )
                cls = import_plugin_class(cls_path)
                registry.register_class(cls, config, name)
                dep_graph[name] = getattr(cls, "dependencies", [])

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
        resource_registry = self.resource_container_cls()
        for cls, config in registry.resource_classes():
            primary_name = getattr(cls, "name", cls.__name__)
            resource_registry.register(primary_name, cls, config)
        await resource_registry.build_all()

        degraded: List[str] = []
        report = await resource_registry.health_report()
        for name, healthy in report.items():
            if not healthy:
                degraded.append(name)
                await resource_registry.remove(name)

        # Phase 3.5: register tools
<<<<<<< HEAD
        tr_cfg = self.config.get("tool_registry", {})
        tool_registry = ToolRegistry(
            concurrency_limit=tr_cfg.get("concurrency_limit", 5),
            cache_ttl=tr_cfg.get("cache_ttl"),
        )
=======
        tool_registry = self.tool_registry_cls()
>>>>>>> c72003e014c664863289e303211be6661160fdc6
        for cls, config in registry.tool_classes():
            if any(dep in degraded for dep in getattr(cls, "dependencies", [])):
                continue
            instance = cls(config)
            await tool_registry.add(getattr(instance, "name", cls.__name__), instance)

        # Phase 4: instantiate prompt and adapter plugins
        plugin_registry = self.plugin_registry_cls()
        for cls, config in registry.non_resource_non_tool_classes():
            if any(dep in degraded for dep in getattr(cls, "dependencies", [])):
                continue
            instance = cls(config)
            stages_cfg = config.get("stages") or config.get("stage")
            if stages_cfg is None:
                stages = getattr(cls, "stages", []) or []
            else:
                stages = stages_cfg if isinstance(stages_cfg, list) else [stages_cfg]
            if not stages:
                raise SystemError(f"No stage specified for {cls.__name__}")
            for stage in stages:
                await plugin_registry.register_plugin_for_stage(
                    instance, PipelineStage.ensure(stage)
                )

        if degraded:
            self.config.setdefault("_disabled_resources", degraded)

        return plugin_registry, resource_registry, tool_registry

    def _validate_dependency_graph(
        self, registry: ClassRegistry, dep_graph: Dict[str, List[str]]
    ) -> None:
        graph = DependencyGraph(dep_graph)
        # Ensure all dependencies reference known plugins before sorting
        for plugin_name, deps in dep_graph.items():
            for dep in deps:
                if not registry.has_plugin(dep):
                    available = registry.list_plugins()
                    raise SystemError(
                        f"Plugin '{plugin_name}' requires '{dep}' but it's not registered. "
                        f"Available: {available}"
                    )

        graph.topological_sort()
