from __future__ import annotations

from pathlib import Path
from typing import Any, List

import yaml

from entity.workflow.workflow import Workflow, WorkflowConfigError

TEMPLATES_DIR = Path(__file__).parent


class TemplateNotFoundError(FileNotFoundError):
    """Raised when a requested template does not exist."""


def list_templates() -> List[str]:
    """Return available template names without extensions."""
    return [p.stem for p in TEMPLATES_DIR.glob("*.yaml")]


def load_template(name: str, resources: dict[str, Any], **params: Any) -> Workflow:
    """Load a workflow template by name and substitute parameters."""
    path = TEMPLATES_DIR / f"{name}.yaml"
    if not path.exists():
        raise TemplateNotFoundError(name)

    text = path.read_text()
    if params:
        try:
            text = text.format(**params)
        except KeyError as exc:
            missing = ", ".join(sorted(set(exc.args)))
            raise ValueError(f"Missing template parameters: {missing}") from exc

    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise WorkflowConfigError("Template must define a mapping")
    return Workflow.from_dict(data, resources)
