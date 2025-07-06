from __future__ import annotations

import os
from typing import Any

from ..exceptions import ResourceError


def interpolate_env_vars(config: Any) -> Any:
    """Recursively replace ``${VAR}`` strings with environment variables."""
    if isinstance(config, dict):
        return {k: interpolate_env_vars(v) for k, v in config.items()}
    if isinstance(config, list):
        return [interpolate_env_vars(item) for item in config]
    if isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        key = config[2:-1]
        value = os.environ.get(key)
        if value is None:
            raise ResourceError(f"Required environment variable {key} not found")
        return value
    return config
