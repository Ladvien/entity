"""Configuration helpers for the Entity pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from config.environment import load_env
from .utils import interpolate_env_vars


class ConfigLoader:
    """Load and normalize pipeline configuration."""

    @staticmethod
    def from_yaml(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = yaml.safe_load(Path(path).read_text()) or {}
        return interpolate_env_vars(data)

    @staticmethod
    def from_json(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = json.loads(Path(path).read_text() or "{}")
        return interpolate_env_vars(data)

    @staticmethod
    def from_dict(cfg: Dict[str, Any], env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        return interpolate_env_vars(dict(cfg))
