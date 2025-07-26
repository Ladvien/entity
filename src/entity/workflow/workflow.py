from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Dict, Iterable, List, Type

import yaml

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class WorkflowConfigError(Exception):
    """Raised when the workflow configuration is invalid."""


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


@dataclass
class Workflow:
    """Mapping of workflow stages to plugin classes."""

    steps: Dict[str, List[Type[Plugin]]] = field(default_factory=dict)

    def plugins_for(self, stage: str) -> List[Type[Plugin]]:
        """Return plugins configured for ``stage``."""
        return self.steps.get(stage, [])

    @classmethod
    def from_dict(cls, config: Dict[str, Iterable[str | Type[Plugin]]]) -> "Workflow":
        """Build a workflow from a stage-to-plugins mapping."""

        steps: Dict[str, List[Type[Plugin]]] = {}
        for stage, plugins in config.items():
            if stage not in WorkflowExecutor._STAGES:
                raise WorkflowConfigError(f"Unknown stage: {stage}")

            steps[stage] = []
            for plugin in plugins:
                plugin_cls = (
                    _import_string(plugin) if isinstance(plugin, str) else plugin
                )
                if hasattr(plugin_cls, "validate_workflow"):
                    plugin_cls.validate_workflow(stage)
                steps[stage].append(plugin_cls)
        return cls(steps)

    @classmethod
    def from_yaml(cls, path: str) -> "Workflow":
        """Load a workflow configuration from a YAML file."""

        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise WorkflowConfigError("Workflow configuration must be a mapping")
        return cls.from_dict(data)
