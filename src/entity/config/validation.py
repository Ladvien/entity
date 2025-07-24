"""Configuration validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from ..workflow.workflow import Workflow, WorkflowConfigError
from ..workflow.executor import WorkflowExecutor

REQUIRED_KEYS = {"resources", "workflow"}


def validate_config(path: str | Path) -> Dict[str, Any]:
    """Load and validate a YAML configuration file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - simple parse error
        raise ValueError(f"Invalid YAML syntax in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Configuration must be a mapping")

    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing required keys: {', '.join(sorted(missing))}")

    return data


def validate_workflow(workflow: Workflow) -> None:
    """Validate plugin stages for a ``Workflow``."""
    for stage, plugins in workflow.steps.items():
        if stage not in WorkflowExecutor._STAGES:
            raise WorkflowConfigError(f"Unknown stage: {stage}")
        for plugin_cls in plugins:
            plugin_cls.validate_workflow(stage)
