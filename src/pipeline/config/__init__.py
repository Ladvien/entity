"""Configuration helpers for the Entity pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from config.environment import load_env
<<<<<<< HEAD
=======
from config.models import validate_config
>>>>>>> 87fc8711f18eb3dd3bc6e63d717bd8ba25a4c47c

from .utils import interpolate_env_vars


class ConfigLoader:
    """Load and normalize pipeline configuration."""

    @staticmethod
    def from_yaml(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = yaml.safe_load(Path(path).read_text()) or {}
        data = interpolate_env_vars(data)
        validate_config(data)
        return data

    @staticmethod
    def from_json(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = json.loads(Path(path).read_text() or "{}")
        data = interpolate_env_vars(data)
        validate_config(data)
        return data

    @staticmethod
    def from_dict(cfg: Dict[str, Any], env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = interpolate_env_vars(dict(cfg))
        validate_config(data)
        return data
