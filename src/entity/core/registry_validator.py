"""Helpers for validating plugin dependencies and stage assignments."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Dict, List

from entity.core.resources.container import DependencyGraph

SRC_PATH = pathlib.Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from entity.core.plugin_utils import import_plugin_class  # noqa: E402


class ClassRegistry:
    def __init__(self) -> None:
        self._classes: Dict[str, type] = {}
        self._configs: Dict[str, Dict] = {}
        self._order: List[str] = []

    def register_class(self, plugin_class: type, config: Dict, name: str) -> None:
        self._classes[name] = plugin_class
        self._configs[name] = config
        self._order.append(name)

    def has_plugin(self, name: str) -> bool:
        return name in self._classes

    def list_plugins(self) -> List[str]:
        return list(self._order)

    def all_plugin_classes(self):
        for name in self._order:
            yield self._classes[name], self._configs[name]


class SystemInitializer:
    def __init__(self, config: Dict) -> None:
        self.config = config

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SystemInitializer":
        import yaml

        with open(yaml_path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return cls(data)


from entity.utils.logging import get_logger  # noqa: E402

from pipeline.utils import resolve_stages  # noqa: E402
from .stages import PipelineStage  # noqa: E402

logger = get_logger(__name__)


class RegistryValidator:
    """Validate plugin registry configuration without initializing resources."""

    def __init__(self, config_path: str) -> None:
        self.initializer = SystemInitializer.from_yaml(config_path)
        self.registry = ClassRegistry()
        self.dep_graph: Dict[str, List[str]] = {}
        self.has_vector_memory = False
        self.has_complex_prompt = False
        self.has_postgres = False
        self.uses_pg_vector_store = False

    def _register_classes(self) -> None:
        plugins_cfg = self.initializer.config.get("plugins", {})
        for section in ["resources", "tools", "adapters", "prompts"]:
            for name, cfg in plugins_cfg.get(section, {}).items():
                cls = import_plugin_class(cfg.get("type", name))
                self.registry.register_class(cls, cfg, name)
                self.dep_graph[name] = list(getattr(cls, "dependencies", []))
                self._validate_stage_assignment(name, cls)

                if name == "memory" and isinstance(cfg, dict):
                    if cfg.get("vector_store"):
                        self.has_vector_memory = True
                        vs_type = cfg["vector_store"].get("type", "")
                        if vs_type.endswith("PgVectorStore"):
                            self.uses_pg_vector_store = True
                if name == "vector_store" or cls.__name__ == "PgVectorStore":
                    self.has_vector_memory = True
                    if cls.__name__ == "PgVectorStore":
                        self.uses_pg_vector_store = True
                if name == "complex_prompt" or cls.__name__ == "ComplexPrompt":
                    self.has_complex_prompt = True
                if name == "database" and cls.__name__ == "PostgresResource":
                    self.has_postgres = True

    @staticmethod
    def _type_default_stages(cls: type) -> list[PipelineStage]:
        from entity.core.plugins.base import AdapterPlugin, PromptPlugin, ToolPlugin

        if issubclass(cls, ToolPlugin):
            return [PipelineStage.DO]
        if issubclass(cls, PromptPlugin):
            return [PipelineStage.THINK]
        if issubclass(cls, AdapterPlugin):
            return [PipelineStage.INPUT, PipelineStage.OUTPUT]
        return []

    @staticmethod
    def _validate_stage_assignment(name: str, cls: type) -> None:
        from entity.core.plugins import ResourcePlugin, ToolPlugin

        if issubclass(cls, (ResourcePlugin, ToolPlugin)):
            return

        attr_stages = getattr(cls, "stages", [])
        type_defaults = RegistryValidator._type_default_stages(cls)
        if not (attr_stages or type_defaults):
            type_defaults = [PipelineStage.THINK]

        stages, _ = resolve_stages(
            cls.__name__,
            cfg_value=None,
            attr_stages=attr_stages,
            explicit_attr=bool(attr_stages),
            type_defaults=type_defaults,
            ensure_stage=PipelineStage.ensure,
            logger=logger,
            error_type=SystemError,
        )

        invalid = [s for s in stages if not isinstance(s, PipelineStage)]
        if invalid:
            raise SystemError(f"Plugin '{name}' has invalid stage values: {invalid}")

    def _validate_dependencies(self) -> None:
        for cls, _ in self.registry.all_plugin_classes():
            validate = getattr(cls, "validate_dependencies", None)
            if validate is None:
                from entity.core.plugins import ValidationResult

                result = ValidationResult.success_result()
            else:
                result = validate(self.registry)
            if not result.success:
                raise SystemError(
                    f"Dependency validation failed for {cls.__name__}: {result.message}"
                )

        graph_map: Dict[str, List[str]] = {name: [] for name in self.dep_graph}
        for plugin_name, deps in self.dep_graph.items():
            for dep in deps:
                optional = dep.endswith("?")
                dep_name = dep[:-1] if optional else dep
                if not self.registry.has_plugin(dep_name):
                    if optional:
                        continue
                    available = self.registry.list_plugins()
                    raise SystemError(
                        (
                            f"Plugin '{plugin_name}' requires '{dep_name}' but it's not registered. "
                            f"Available: {available}"
                        )
                    )
                if dep_name in graph_map:
                    graph_map[dep_name].append(plugin_name)

        DependencyGraph(graph_map).topological_sort()

    def _validate_configs(self) -> None:
        for cls, cfg in self.registry.all_plugin_classes():
            validate = getattr(cls, "validate_config", None)
            if validate is None:
                from entity.core.plugins import ValidationResult

                result = ValidationResult.success_result()
            else:
                result = validate(cfg)
            if not result.success:
                raise SystemError(
                    f"Config validation failed for {cls.__name__}: {result.message}"
                )

    def run(self) -> None:
        self._register_classes()
        self._validate_dependencies()
        self._validate_configs()
        if self.has_complex_prompt and not self.has_vector_memory:
            raise SystemError(
                "ComplexPrompt requires the memory resource with a vector store"
            )
        if self.uses_pg_vector_store and not self.has_postgres:
            raise SystemError(
                "PgVectorStore vector store requires the PostgresResource to be registered"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate plugin dependencies and stage assignments"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the YAML configuration file",
    )
    args = parser.parse_args()

    try:
        RegistryValidator(args.config).run()
    except SystemError as exc:  # pragma: no cover - CLI only
        logger.error("Validation failed: %s", exc)
        raise SystemExit(1)
    logger.info("Validation succeeded")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
