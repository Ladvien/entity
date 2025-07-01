from __future__ import annotations

import copy
import json
import os
from contextlib import contextmanager
from importlib import import_module
from typing import Any, Dict, Iterable, List, Tuple

from config.environment import load_env

from .base_plugins import BasePlugin, ResourcePlugin, ToolPlugin
from .defaults import DEFAULT_CONFIG
from .registries import PluginRegistry, ResourceRegistry, ToolRegistry

LLM_PROVIDERS = {
    "openai": "pipeline.plugins.resources.openai:OpenAIResource",
    "ollama": "pipeline.plugins.resources.ollama_llm:OllamaLLMResource",
    "gemini": "pipeline.plugins.resources.gemini:GeminiResource",
    "claude": "pipeline.plugins.resources.claude:ClaudeResource",
}


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

    def resource_classes(self) -> Iterable[Tuple[type[ResourcePlugin], Dict]]:
        for name, cls in self._classes.items():
            if issubclass(cls, ResourcePlugin):
                yield cls, self._configs[name]

    def tool_classes(self) -> Iterable[Tuple[type[ToolPlugin], Dict]]:
        for name, cls in self._classes.items():
            if issubclass(cls, ToolPlugin):
                yield cls, self._configs[name]

    def non_resource_non_tool_classes(self) -> Iterable[Tuple[type[BasePlugin], Dict]]:
        for name, cls in self._classes.items():
            if not issubclass(cls, ResourcePlugin) and not issubclass(cls, ToolPlugin):
                yield cls, self._configs[name]


def import_plugin_class(path: str) -> type[BasePlugin]:
    """Import plugin class from module path 'module.submodule:ClassName'."""
    if ":" in path:
        module_path, class_name = path.split(":", 1)
    elif "." in path:
        module_path, class_name = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid plugin path: {path}")
    module = import_module(module_path)
    return getattr(module, class_name)


@contextmanager
def initialization_cleanup_context():
    try:
        yield
    finally:
        pass


class SystemInitializer:
    """Initialize and validate all plugins for the pipeline.

    Applies **Fail-Fast Validation (15)** and **Load-Time Validation (20)**
    by verifying configuration and dependencies before any plugin runs.
    """

    def __init__(self, config: Dict | None = None, env_file: str = ".env") -> None:
        load_env(env_file)
        self.config = config or copy.deepcopy(DEFAULT_CONFIG)

    @classmethod
    def from_yaml(cls, yaml_path: str, env_file: str = ".env") -> "SystemInitializer":
        import yaml

        with open(yaml_path, "r") as fh:
            content = fh.read()
        config = yaml.safe_load(content)
        load_env(env_file)
        config = cls._interpolate_env_vars(config)
        return cls(config, env_file)

    @classmethod
    def from_json(cls, json_path: str, env_file: str = ".env") -> "SystemInitializer":
        with open(json_path, "r") as fh:
            content = fh.read()
        config = json.loads(content or "{}")
        load_env(env_file)
        config = cls._interpolate_env_vars(config)
        return cls(config, env_file)

    @classmethod
    def from_dict(
        cls, cfg: Dict[str, Any], env_file: str = ".env"
    ) -> "SystemInitializer":
        load_env(env_file)
        config = cls._interpolate_env_vars(dict(cfg))
        return cls(config, env_file)

    def get_resource_config(self, name: str) -> Dict:
        return self.config["plugins"]["resources"][name]

    def get_tool_config(self, name: str) -> Dict:
        return self.config["plugins"]["tools"][name]

    def get_adapter_config(self, name: str) -> Dict:
        return self.config["plugins"]["adapters"][name]

    def get_prompt_config(self, name: str) -> Dict:
        return self.config["plugins"]["prompts"][name]

    async def initialize(self):
        self._apply_llm_provider()
        registry = ClassRegistry()
        dep_graph: Dict[str, List[str]] = {}

        # Phase 1: register all plugin classes
        resources = self.config.get("plugins", {}).get("resources", {})
        for name, config in resources.items():
            cls = import_plugin_class(config.get("type", name))
            registry.register_class(cls, config, name)
            dep_graph[name] = getattr(cls, "dependencies", [])

        for section in ["tools", "adapters", "prompts"]:
            for name, config in self.config.get("plugins", {}).get(section, {}).items():
                cls = import_plugin_class(config.get("type", name))
                registry.register_class(cls, config, name)
                dep_graph[name] = getattr(cls, "dependencies", [])

        # Validate dependencies declared by each plugin class
        for plugin_class, _ in registry.all_plugin_classes():
            result = plugin_class.validate_dependencies(registry)
            if not result.success:
                raise SystemError(
                    f"Dependency validation failed for {plugin_class.__name__}: "
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

        # Phase 3: initialize resources
        resource_registry = ResourceRegistry()
        for cls, config in registry.resource_classes():
            instance = cls(config)
            if hasattr(instance, "initialize") and callable(
                getattr(instance, "initialize")
            ):
                await instance.initialize()
            primary_name = getattr(instance, "name", cls.__name__)
            resource_registry.add(primary_name, instance)
            for alias in getattr(instance, "aliases", []):
                if alias != primary_name:
                    resource_registry.add(alias, instance)

        # Phase 3.5: register tools
        tool_registry = ToolRegistry()
        for cls, config in registry.tool_classes():
            instance = cls(config)
            tool_registry.add(getattr(instance, "name", cls.__name__), instance)

        # Phase 4: instantiate prompt and adapter plugins
        plugin_registry = PluginRegistry()
        for cls, config in registry.non_resource_non_tool_classes():
            instance = cls(config)
            for stage in getattr(cls, "stages", []):
                plugin_registry.register_plugin_for_stage(instance, stage)

        return plugin_registry, resource_registry, tool_registry

    def _validate_dependency_graph(
        self, registry: ClassRegistry, dep_graph: Dict[str, List[str]]
    ):
        for plugin_name, dependencies in dep_graph.items():
            for dep in dependencies:
                if not registry.has_plugin(dep):
                    available = registry.list_plugins()
                    raise SystemError(
                        (
                            f"Plugin '{plugin_name}' requires '{dep}' but it's not registered. "
                            f"Available: {available}"
                        )
                    )

        in_degree = {node: 0 for node in dep_graph}
        for node in dep_graph:
            for neighbor in dep_graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        queue = [n for n, deg in in_degree.items() if deg == 0]
        processed: List[str] = []
        while queue:
            current = queue.pop(0)
            processed.append(current)
            for neighbor in dep_graph[current]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(processed) != len(in_degree):
            cycle_nodes = [n for n in in_degree if n not in processed]
            raise SystemError(f"Circular dependency detected involving: {cycle_nodes}")

    @staticmethod
    def _interpolate_env_vars(config: Any) -> Any:
        if isinstance(config, dict):
            return {
                k: SystemInitializer._interpolate_env_vars(v) for k, v in config.items()
            }
        if isinstance(config, list):
            return [SystemInitializer._interpolate_env_vars(i) for i in config]
        if isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            key = config[2:-1]
            value = os.environ.get(key)
            if value is None:
                raise EnvironmentError(f"Required environment variable {key} not found")
            return value
        return config

    def _apply_llm_provider(self) -> None:
        resources = self.config.get("plugins", {}).get("resources", {})
        llm_cfg = resources.get("llm")
        if llm_cfg and "provider" in llm_cfg and "type" not in llm_cfg:
            provider = str(llm_cfg["provider"]).lower()
            if provider not in LLM_PROVIDERS:
                raise ValueError(f"Unknown LLM provider '{provider}'")
            llm_cfg["type"] = LLM_PROVIDERS[provider]
