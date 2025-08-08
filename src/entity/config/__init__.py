"""Configuration utilities.

This module provides helpers for loading and validating configuration files. It
also offers `${VAR}` style environment variable substitution with cycle
detection and optional ``.env`` loading.
Errors raised during substitution use :class:`SubstitutionError` for clarity.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from entity.config.validation import ConfigModel


class SubstitutionError(ValueError):
    """Raised when environment variable substitution fails."""

    pass


class VariableResolver:
    """Resolve ``${VAR}`` patterns recursively with cycle detection."""

    _pattern = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, env_file: str | None = None) -> None:
        self.env: dict[str, str] = dict(os.environ)
        self._load_env_file(env_file)

    def _load_env_file(self, env_file: str | None) -> None:
        env_path = Path(env_file or ".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                self.env.setdefault(key.strip(), val.strip())

    def substitute(self, obj: Any) -> Any:
        """Recursively substitute environment variables in ``obj``."""
        if isinstance(obj, dict):
            return {k: self.substitute(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.substitute(v) for v in obj]
        if isinstance(obj, str):
            return self._resolve_value(obj, [])
        return obj

    def _resolve_value(self, value: str, stack: list[str]) -> str:
        def replace(match: re.Match[str]) -> str:
            var = match.group(1)
            if var in stack:
                cycle = " -> ".join(stack + [var])
                raise SubstitutionError(f"Circular reference detected: {cycle}")
            if var not in self.env:
                raise SubstitutionError(f"Environment variable '{var}' not found")
            return self._resolve_value(self.env[var], stack + [var])

        return self._pattern.sub(replace, value)

    @staticmethod
    def substitute_variables(obj: Any, env_file: str | None = None) -> Any:
        """Public helper to substitute environment variables in ``obj``."""
        resolver = VariableResolver(env_file)
        return resolver.substitute(obj)


@lru_cache(maxsize=32)
def _cached_validate(path: str) -> ConfigModel:
    """Internal helper cached by path."""

    return ConfigModel.validate_config(path)


def load_config(path: str | Path) -> ConfigModel:
    """Load and validate ``path`` with caching."""

    resolved = str(Path(path).resolve())
    return _cached_validate(resolved)


def clear_config_cache() -> None:
    """Reset the internal configuration cache."""

    _cached_validate.cache_clear()


__all__ = [
    "ConfigModel",
    "SubstitutionError",
    "VariableResolver",
    "load_config",
    "clear_config_cache",
]
