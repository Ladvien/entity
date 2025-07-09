from __future__ import annotations

"""Minimal environment loader used for tests."""

from pathlib import Path
import os


def load_env(path: str | Path = ".env") -> None:
    """Load key=value pairs from ``path`` into ``os.environ`` if file exists."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)
