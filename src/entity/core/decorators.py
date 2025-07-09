from __future__ import annotations

"""Helpers for defining Entity plugins via decorators."""

from typing import Any, Callable, Optional

from .plugin_utils import PluginAutoClassifier


def plugin(func: Optional[Callable] = None, **hints: Any) -> Callable:
    """Decorator turning ``func`` into a plugin."""

    def decorator(f: Callable) -> Callable:
        plugin_obj = PluginAutoClassifier.classify(f, hints)
        setattr(f, "__entity_plugin__", plugin_obj)
        return f

    return decorator(func) if func else decorator
