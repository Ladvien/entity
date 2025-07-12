from __future__ import annotations

"""Environment helpers for Entity."""

from pathlib import Path
from typing import Any, MutableMapping, Mapping

import yaml

from dotenv import load_dotenv


def load_env(env_file: str | Path = ".env") -> None:
    """Load environment variables from ``env_file`` if it exists."""
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)


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
