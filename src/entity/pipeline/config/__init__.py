"""Configuration helpers for the Entity pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from entity.config.environment import load_env
from entity.config.models import validate_config
from ..workflow import Workflow

from .utils import interpolate_env_vars


class ConfigLoader:
    """Load and normalize pipeline configuration."""

    @staticmethod
    def _load_workflow(workflow: Any, base: Path) -> Workflow:
        """Return :class:`Workflow` from mapping or file path."""
        if isinstance(workflow, Workflow):
            return workflow
        if isinstance(workflow, str):
            wf_path = (
                (base / workflow)
                if not Path(workflow).is_absolute()
                else Path(workflow)
            )
            if wf_path.suffix in {".yaml", ".yml"}:
                wf_data = yaml.safe_load(wf_path.read_text()) or {}
            else:
                wf_data = json.loads(wf_path.read_text() or "{}")
        elif isinstance(workflow, dict):
            wf_data = workflow
        else:
            raise TypeError("workflow must be a path or mapping")
        wf_data = interpolate_env_vars(wf_data)
        return Workflow.from_dict(wf_data)

    @staticmethod
    def from_yaml(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        path_obj = Path(path)
        data = yaml.safe_load(path_obj.read_text()) or {}
        data = interpolate_env_vars(data)
        if "workflow" in data:
            data["workflow"] = ConfigLoader._load_workflow(
                data["workflow"], path_obj.parent
            )
        validate_config(data)
        return data

    @staticmethod
    def from_json(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        path_obj = Path(path)
        data = json.loads(path_obj.read_text() or "{}")
        data = interpolate_env_vars(data)
        if "workflow" in data:
            data["workflow"] = ConfigLoader._load_workflow(
                data["workflow"], path_obj.parent
            )
        validate_config(data)
        return data

    @staticmethod
    def from_dict(cfg: Dict[str, Any], env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = interpolate_env_vars(dict(cfg))
        if "workflow" in data:
            data["workflow"] = ConfigLoader._load_workflow(data["workflow"], Path("."))
        validate_config(data)
        return data
