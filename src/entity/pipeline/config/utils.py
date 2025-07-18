from __future__ import annotations

"""Utility helpers for configuration loading."""

import os
import re
from typing import Any

_PATTERN = re.compile(r"\$\{([^}]+)\}")


def interpolate_env_vars(value: Any) -> Any:
    """Recursively replace ``${VAR}`` with environment variables."""
    if isinstance(value, dict):
        return {k: interpolate_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate_env_vars(v) for v in value]
    if isinstance(value, str):
        return _PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(0)), value)
    return value


__all__ = ["interpolate_env_vars"]
