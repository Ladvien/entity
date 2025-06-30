"""Configuration helpers for the Entity pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml

from src.config.environment import load_env


def _interpolate_env_vars(config: Any) -> Any:
    """Recursively replace ${VAR} in config with environment variables."""
    if isinstance(config, dict):
        return {k: _interpolate_env_vars(v) for k, v in config.items()}
    if isinstance(config, list):
        return [_interpolate_env_vars(item) for item in config]
    if isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        key = config[2:-1]
        value = os.environ.get(key)
        if value is None:
            raise EnvironmentError(f"Required environment variable {key} not found")
        return value
    return config


class ConfigLoader:
    """Load and normalize pipeline configuration."""

    @staticmethod
    def from_yaml(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = yaml.safe_load(Path(path).read_text()) or {}
        return _interpolate_env_vars(data)

    @staticmethod
    def from_json(path: str | Path, env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        data = json.loads(Path(path).read_text() or "{}")
        return _interpolate_env_vars(data)

    @staticmethod
    def from_dict(cfg: Dict[str, Any], env_file: str = ".env") -> Dict[str, Any]:
        load_env(env_file)
        return _interpolate_env_vars(dict(cfg))
