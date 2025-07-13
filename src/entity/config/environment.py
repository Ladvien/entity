"""Environment helpers for Entity."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, MutableMapping, Mapping

import yaml

from dotenv import dotenv_values
from dotenv import load_dotenv


class EnvironmentLoader:
    """Load configuration variables from .env and secrets files."""

    def __init__(self, env_file: str | Path = ".env", env: str | None = None) -> None:
        self.env_path = Path(env_file)
        self.env = env

    def _collect_values(self) -> dict[str, str]:
        values = dotenv_values(self.env_path) if self.env_path.exists() else {}
        if self.env:
            secret_path = Path("secrets") / f"{self.env}.env"
            if secret_path.exists():
                values.update(dotenv_values(secret_path))
        return values

    def load(self) -> None:
        for key, value in self._collect_values().items():
            os.environ.setdefault(key, value)

        load_dotenv(self.env_path, override=False)


def load_env(env_file: str | Path = ".env", env: str | None = None) -> None:
    """Convenience wrapper around :class:`EnvironmentLoader`."""

    EnvironmentLoader(env_file, env).load()


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


def _load_with_extends(path: Path) -> dict[str, Any]:
    """Load YAML from ``path`` resolving optional ``extends`` chain."""

    data = yaml.safe_load(path.read_text()) or {}
    parent = data.pop("extends", None)
    if parent:
        parent_path = Path(parent)
        if not parent_path.exists():
            parent_path = path.parent / f"{parent}.yaml"
        if parent_path.exists():
            base = _load_with_extends(parent_path)
            data = _merge(base, data)
    return data


def load_config(base: str | Path, overlay: str | Path | None = None) -> dict[str, Any]:
    """Return configuration from ``base`` merged with optional ``overlay``.

    Both files may specify ``extends`` to inherit settings from another
    configuration file located in the same directory or referenced by path.
    """

    base_data = _load_with_extends(Path(base))
    if overlay:
        overlay_path = Path(overlay)
        if overlay_path.exists():
            overlay_data = _load_with_extends(overlay_path)
            base_data = _merge(base_data, overlay_data)
    return _interpolate(base_data)  # type: ignore[no-any-return]


__all__ = ["load_env", "load_config"]
