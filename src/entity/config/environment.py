"""Environment helpers for Entity."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, MutableMapping, Mapping

import yaml

from dotenv import load_dotenv, dotenv_values


def load_env(env_file: str | Path = ".env", env: str | None = None) -> None:
    """Load variables from ``env_file`` and ``secrets/<env>.env``.

    Existing process variables are never overwritten. Values from
    ``secrets/<env>.env`` override entries from ``env_file`` when both
    are present.
    """

    env_values: dict[str, str] = {}

    env_path = Path(env_file)
    if env_path.exists():
        env_values.update(dotenv_values(env_path))

    env_name = env or os.getenv("ENTITY_ENV")
    if env_name:
        secret_path = Path("secrets") / f"{env_name}.env"
        if secret_path.exists():
            env_values.update(dotenv_values(secret_path))

    for key, value in env_values.items():
        os.environ.setdefault(key, value)


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


def load_config(base: str | Path, overlay: str | Path | None = None) -> dict[str, Any]:
    """Return configuration from ``base`` merged with optional ``overlay``."""

    base_data = yaml.safe_load(Path(base).read_text()) or {}
    if overlay:
        overlay_path = Path(overlay)
        if overlay_path.exists():
            overlay_data = yaml.safe_load(overlay_path.read_text()) or {}
            base_data = _merge(base_data, overlay_data)
    return base_data


__all__ = ["load_env", "load_config"]
