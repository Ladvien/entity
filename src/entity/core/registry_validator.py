"""Helpers for validating plugin dependencies and stage assignments."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Dict, List

from pipeline.utils import DependencyGraph

SRC_PATH = pathlib.Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pipeline.initializer import ClassRegistry  # noqa: E402
from pipeline.initializer import SystemInitializer  # noqa: E402
from pipeline.initializer import import_plugin_class  # noqa: E402
from entity.utils.logging import get_logger  # noqa: E402
from pipeline.stages import PipelineStage  # noqa: E402

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

                if name == "vector_memory" or cls.__name__ == "PgVectorStore":
                    self.has_vector_memory = True
                    if cls.__name__ == "PgVectorStore":
                        self.uses_pg_vector_store = True
                if name == "complex_prompt" or cls.__name__ == "ComplexPrompt":
                    self.has_complex_prompt = True
                if name == "database" and cls.__name__ == "PostgresResource":
                    self.has_postgres = True

    @staticmethod
    def _validate_stage_assignment(name: str, cls: type) -> None:
        from pipeline.resources import Resource
        from pipeline.base_plugins import ResourcePlugin, ToolPlugin

        if issubclass(cls, (ResourcePlugin, Resource, ToolPlugin)):
            return

        stages = getattr(cls, "stages", None)
        if not stages:
            raise SystemError(f"Plugin '{name}' does not specify any stages")
        invalid = [s for s in stages if not isinstance(s, PipelineStage)]
        if invalid:
            raise SystemError(f"Plugin '{name}' has invalid stage values: {invalid}")

    def _validate_dependencies(self) -> None:
        for cls, _ in self.registry.all_plugin_classes():
            validate = getattr(cls, "validate_dependencies", None)
            if validate is None:
                from pipeline.validation import ValidationResult

                result = ValidationResult.success_result()
            else:
                try:
                    result = validate(self.registry)
                except NameError as exc:  # pragma: no cover - legacy plugins
                    if "ValidationResult" in str(exc):
                        from pipeline.validation import ValidationResult

                        result = ValidationResult.success_result()
                    else:
                        raise
            if not result.success:
                raise SystemError(
                    f"Dependency validation failed for {cls.__name__}: {result.error_message}"
                )

        graph = DependencyGraph(self.dep_graph)
        for plugin_name, deps in self.dep_graph.items():
            for dep in deps:
                if not self.registry.has_plugin(dep):
                    available = self.registry.list_plugins()
                    raise SystemError(
                        (
                            f"Plugin '{plugin_name}' requires '{dep}' but it's not registered. "
                            f"Available: {available}"
                        )
                    )

        graph.topological_sort()

    def run(self) -> None:
        self._register_classes()
        self._validate_dependencies()
        if self.has_complex_prompt and not self.has_vector_memory:
            raise SystemError(
                "ComplexPrompt requires the 'vector_memory' resource to be registered"
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
