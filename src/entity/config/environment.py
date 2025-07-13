"""Environment helpers for Entity."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, MutableMapping, Mapping

import yaml

from dotenv import dotenv_values


def load_env(env_file: str | Path = ".env", env: str | None = None) -> None:
    """Load variables from ``env_file`` and optional ``secrets/<env>.env``.

    Existing environment variables are never overwritten. When both files
    define the same key, the secrets file takes precedence over ``env_file``.
    """

    env_path = Path(env_file)
    original_keys = set(os.environ)

    if env_path.exists():
        values = dotenv_values(env_path)
        for key, value in values.items():
            if key not in original_keys:
                os.environ[key] = value

    secret_path: Path | None = None
    if env:
        secret_path = Path("secrets") / f"{env}.env"
        if secret_path.exists():
            values = dotenv_values(secret_path)
            for key, value in values.items():
                if key not in original_keys:
                    os.environ[key] = value


def _merge(
    base: MutableMapping[str, Any], overlay: Mapping[str, Any]
) -> MutableMapping[str, Any]:
    """Recursively merge ``overlay`` into ``base``."""

    for key, value in overlay.items():
        if (
            key in base
            and isinstance(base[key], MutableMapping)
            and isinstance(value, Mapping)
        ):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _interpolate(value: Any) -> Any:
    """Recursively substitute ``${VAR}`` with environment values."""
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    if isinstance(value, str):
        return _PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(0)), value)
    return value


def load_config(base: str | Path, overlay: str | Path | None = None) -> dict[str, Any]:
    """Return configuration from ``base`` merged with optional ``overlay``."""

    base_data = yaml.safe_load(Path(base).read_text()) or {}
    if overlay:
        overlay_path = Path(overlay)
        if overlay_path.exists():
            overlay_data = yaml.safe_load(overlay_path.read_text()) or {}
            base_data = _merge(base_data, overlay_data)
    return _interpolate(base_data)  # type: ignore[no-any-return]


__all__ = ["load_env", "load_config"]
