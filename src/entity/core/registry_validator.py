"""Helpers for validating plugin dependencies and stage assignments."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import pathlib
import sys
from typing import Dict, List

from entity.core.resources.container import DependencyGraph
from entity.core.registries import PluginRegistry

SRC_PATH = pathlib.Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from entity.core.plugin_utils import import_plugin_class  # noqa: E402


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

from .stages import PipelineStage  # noqa: E402

logger = get_logger(__name__)


class RegistryValidator:
    """Validate plugin registry configuration without initializing resources."""

    def __init__(self, config_path: str) -> None:
        self.initializer = SystemInitializer.from_yaml(config_path)
        self.registry = PluginRegistry()
        self.dep_graph: Dict[str, List[str]] = {}
        self.has_vector_memory = False
        self.has_complex_prompt = False
        self.has_postgres = False
        self.uses_pg_vector_store = False

    @staticmethod
    def _validate_plugin_type(name: str, cls: type, section: str) -> None:
        """Ensure plugin belongs to the expected base class."""
        from entity.core.plugins import (
            AdapterPlugin,
            InfrastructurePlugin,
            InputAdapterPlugin,
            OutputAdapterPlugin,
            PromptPlugin,
            ResourcePlugin,
            ToolPlugin,
        )

        if section == "infrastructure" and not issubclass(cls, InfrastructurePlugin):
            raise SystemError(
                f"Plugin '{name}' in '{section}' must inherit from InfrastructurePlugin"
            )
        if section in {
            "resources",
            "agent_resources",
            "custom_resources",
        } and not issubclass(cls, ResourcePlugin):
            raise SystemError(
                f"Plugin '{name}' in '{section}' must inherit from ResourcePlugin"
            )
        if section == "tools" and not issubclass(cls, ToolPlugin):
            raise SystemError(
                f"Plugin '{name}' in '{section}' must inherit from ToolPlugin"
            )
        if section == "adapters" and not issubclass(
            cls, (AdapterPlugin, InputAdapterPlugin, OutputAdapterPlugin)
        ):
            raise SystemError(
                f"Plugin '{name}' in '{section}' must inherit from AdapterPlugin"
            )
        if section == "prompts" and not issubclass(cls, PromptPlugin):
            raise SystemError(
                f"Plugin '{name}' in '{section}' must inherit from PromptPlugin"
            )

    def _register_classes(self) -> None:
        plugins_cfg = self.initializer.config.get("plugins", {}) or {}
        for section in [
            "resources",
            "agent_resources",
            "infrastructure",
            "tools",
            "adapters",
            "prompts",
        ]:
            section_cfg = plugins_cfg.get(section) or {}
            for name, cfg in section_cfg.items():
                cls = import_plugin_class(cfg.get("type", name))
                self._validate_plugin_type(name, cls, section)
                cfg_deps = list(cfg.get("dependencies", []))
                class_deps = list(getattr(cls, "dependencies", []))
                deps = cfg_deps or class_deps
                self.registry.register_plugin(cls, name, dependencies=deps, config=cfg)
                self.dep_graph[name] = deps
                self._validate_stage_assignment(name, cls, cfg)

                if name == "vector_store" or cls.__name__ == "PgVectorStore":
                    self.has_vector_memory = True
                    if cls.__name__ == "PgVectorStore":
                        self.uses_pg_vector_store = True
                if name == "complex_prompt" or cls.__name__ == "ComplexPrompt":
                    self.has_complex_prompt = True
                if name == "database" and cls.__name__ == "PostgresResource":
                    self.has_postgres = True

    @staticmethod
    def _validate_stage_assignment(name: str, cls: type, cfg: Dict) -> None:
        from entity.core.plugins import (
            AdapterPlugin,
            InputAdapterPlugin,
            OutputAdapterPlugin,
            ResourcePlugin,
            ToolPlugin,
            InfrastructurePlugin,
        )

        if issubclass(cls, (ResourcePlugin, InfrastructurePlugin)):
            if cfg.get("stage") or cfg.get("stages") or getattr(cls, "stages", None):
                raise SystemError(
                    f"Resource plugin '{name}' should not define pipeline stages"
                )
            return

        cfg_value = cfg.get("stages") or cfg.get("stage")
        if cfg_value is not None:
            stages = cfg_value if isinstance(cfg_value, list) else [cfg_value]
            explicit = True
        else:
            stages = getattr(cls, "stages", [])
            explicit = bool(stages)

        if not explicit:
            raise SystemError(f"Plugin '{name}' does not specify any stages")

        stages = [PipelineStage.ensure(s) for s in stages]
        invalid = [s for s in stages if not isinstance(s, PipelineStage)]
        if invalid:
            raise SystemError(f"Plugin '{name}' has invalid stage values: {invalid}")

        if issubclass(cls, ToolPlugin) and any(s != PipelineStage.DO for s in stages):
            raise SystemError("ToolPlugin must execute only in the DO stage")
        if issubclass(cls, InputAdapterPlugin) and any(
            s != PipelineStage.INPUT for s in stages
        ):
            raise SystemError("InputAdapterPlugin must execute only in the INPUT stage")
        if issubclass(cls, OutputAdapterPlugin) and any(
            s != PipelineStage.OUTPUT for s in stages
        ):
            raise SystemError(
                "OutputAdapterPlugin must execute only in the OUTPUT stage"
            )
        if issubclass(cls, AdapterPlugin) and any(
            s not in {PipelineStage.INPUT, PipelineStage.OUTPUT} for s in stages
        ):
            raise SystemError("AdapterPlugin stages must be INPUT and/or OUTPUT")

    def _validate_dependencies(self) -> None:
        self.registry.validate_dependencies()

    def _validate_resource_levels(self) -> None:
        from entity.core.plugins import AgentResource, ResourcePlugin
        from entity.resources.base import AgentResource as CanonicalAgentResource

        for plugin_name in self.registry.list_plugin_names():
            plugin_cls = self.registry.get_class(plugin_name)
            if plugin_cls is None or issubclass(plugin_cls, ResourcePlugin):
                continue
            for dep in self.dep_graph.get(plugin_name, []):
                dep_name = dep[:-1] if dep.endswith("?") else dep
                dep_cls = self.registry.get_class(dep_name)
                if dep_cls is None or issubclass(
                    dep_cls, (AgentResource, CanonicalAgentResource)
                ):
                    continue
                raise SystemError(
                    f"Plugin '{plugin_name}' depends on '{dep_name}' which is not a layer-3 or layer-4 resource"
                )

    def _validate_configs(self) -> None:
        for name in self.registry.list_plugin_names():
            cls = self.registry.get_class(name)
            cfg = self.registry.get_config(name) or {}
            validate = getattr(cls, "validate_config", None)
            if validate is None:
                from entity.core.plugins import ValidationResult

                result = ValidationResult.success_result()
            else:
                clean_cfg = {
                    k: v
                    for k, v in cfg.items()
                    if k not in {"type", "dependencies", "stage", "stages"}
                }
                result = validate(clean_cfg)
                if inspect.isawaitable(result):
                    result = asyncio.run(result)
            if not result.success:
                raise SystemError(
                    f"Config validation failed for {cls.__name__}: {result.message}"
                )

    def run(self) -> None:
        self._register_classes()
        self._validate_dependencies()
        self._validate_resource_levels()
        self._validate_configs()
        if self.has_complex_prompt and not self.has_vector_memory:
            raise SystemError(
                "ComplexPrompt requires the memory resource with a vector store"
            )
        if self.uses_pg_vector_store and not self.has_postgres:
            raise SystemError(
                "PgVectorStore vector store requires the PostgresResource to be registered"
            )

    def graph_dependencies(self) -> str:
        """Return the dependency graph in GraphViz DOT format."""

        lines = ["digraph dependencies {"]
        for plugin, deps in self.dep_graph.items():
            if not deps:
                lines.append(f'    "{plugin}"')
            for dep in deps:
                dep_name = dep[:-1] if dep.endswith("?") else dep
                lines.append(f'    "{plugin}" -> "{dep_name}"')
        lines.append("}")
        return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate plugin dependencies and stage assignments"
    )
    parser.add_argument(
        "--config",
        default="config/dev.yaml",
        help="Path to the YAML configuration file",
    )
    parser.add_argument(
        "--graph",
        help="Write GraphViz dependency graph to the given file. Use '-' for stdout.",
    )
    args = parser.parse_args()

    try:
        validator = RegistryValidator(args.config)
        validator.run()
        if args.graph is not None:
            dot = validator.graph_dependencies()
            if args.graph == "-":
                print(dot)
            else:
                pathlib.Path(args.graph).write_text(dot, encoding="utf-8")
    except SystemError as exc:  # pragma: no cover - CLI only
        logger.error("Validation failed: %s", exc)
        raise SystemExit(1)
    logger.info("Validation succeeded")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
