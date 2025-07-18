from __future__ import annotations

from entity.cli import load_plugin as _load_plugin

__all__ = ["load_plugin"]


def load_plugin(path: str):
    """Load a plugin class from a file path."""
    return _load_plugin(path)
