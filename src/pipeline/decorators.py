from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .plugins.classifier import PluginAutoClassifier


def plugin(func: Optional[Callable] = None, **hints: Any) -> Callable:
    """Decorator to mark ``func`` as a pipeline plugin."""

    def decorator(f: Callable) -> Callable:
        plugin_obj = PluginAutoClassifier.classify(f, hints)
        setattr(f, "__entity_plugin__", plugin_obj)
        return f

    return decorator(func) if func else decorator
