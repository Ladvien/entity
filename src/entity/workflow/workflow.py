from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Dict, Iterable, List, Type, TYPE_CHECKING

import yaml

from entity.plugins.validation import ValidationResult
from entity.config.variable_resolver import VariableResolver

if TYPE_CHECKING:
    from entity.plugins.base import Plugin
    from entity.workflow.executor import WorkflowExecutor


class WorkflowConfigError(Exception):
    """Raised when the workflow configuration is invalid."""


@dataclass
class Workflow:
    """Mapping of workflow stages to plugin classes."""

    steps: Dict[str, List["Plugin"]] = field(default_factory=dict)
    supported_stages: List[str] = field(default_factory=list)

    def plugins_for(self, stage: str) -> List["Plugin"]:
        """Return plugins configured for ``stage``."""
        return self.steps.get(stage, [])

    @classmethod
    def from_dict(cls, config: Dict[str, Iterable[str | Type["Plugin"]]], resources: dict[str, Any]) -> "Workflow":
        """Build a workflow from a stage-to-plugins mapping."""
        from entity.plugins.base import Plugin
        from entity.workflow.executor import WorkflowExecutor

        def _import_string(path: str) -> Type[Plugin]:
            module_path, _, class_name = path.rpartition(".")
            if not module_path:
                raise WorkflowConfigError(f"Invalid plugin path: {path}")
            module = import_module(module_path)
            try:
                plugin_cls = getattr(module, class_name)
            except AttributeError as exc:
                raise WorkflowConfigError(f"Plugin '{path}' not found") from exc
            if not issubclass(plugin_cls, Plugin):
                raise WorkflowConfigError(f"{path} is not a Plugin")
            return plugin_cls

        steps: Dict[str, List[Plugin]] = {}
        workflow_instance = cls(steps, WorkflowExecutor._STAGES)

        for stage, plugins in config.items():
            if stage not in WorkflowExecutor._STAGES:
                raise WorkflowConfigError(f"Unknown stage: {stage}")

            steps[stage] = []
            for plugin_config in plugins:
                plugin_cls = (
                    _import_string(plugin_config) if isinstance(plugin_config, str) else plugin_config
                )
                plugin = plugin_cls(resources, {}) # Pass resources to plugin constructor
                plugin.assigned_stage = stage

                validation_result = plugin.validate_config()
                if not validation_result.success:
                    raise WorkflowConfigError(f"Invalid config for {plugin_cls.__name__}: {validation_result.errors}")

                validation_result = plugin.validate_workflow(workflow_instance)
                if not validation_result.success:
                    raise WorkflowConfigError(f"Invalid workflow for {plugin_cls.__name__}: {validation_result.errors}")

                steps[stage].append(plugin)
        return workflow_instance

    @classmethod
    def from_yaml(cls, path: str, resources: dict[str, Any]) -> "Workflow":
        """Load a workflow configuration from a YAML file."""

        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        data = VariableResolver.substitute_variables(data)
        if not isinstance(data, dict):
            raise WorkflowConfigError("Workflow configuration must be a mapping")
        return cls.from_dict(data, resources)
