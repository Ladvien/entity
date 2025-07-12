from __future__ import annotations

"""Helpers for defining Entity plugins via decorators."""

from typing import Any, Callable, Optional

from .stages import PipelineStage

from .plugin_utils import PluginAutoClassifier


def plugin(func: Optional[Callable] = None, **hints: Any) -> Callable:
    """Decorator turning ``func`` into a plugin."""

    def decorator(f: Callable) -> Callable:
        if not (hints.get("plugin_class") or hints.get("stage") or hints.get("stages")):
            raise ValueError("plugin() requires 'plugin_class' or stage hints")

        suggestion = suggest_upgrade(f)
        if suggestion:
            get_logger(__name__).warning(suggestion)

        plugin_obj = PluginAutoClassifier.classify(f, hints)
        setattr(f, "__entity_plugin__", plugin_obj)
        return f

    return decorator(func) if func else decorator


def input(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for INPUT stage plugins."""

    hints["stage"] = PipelineStage.INPUT
    return plugin(func, **hints)


def parse(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for PARSE stage plugins."""

    hints["stage"] = PipelineStage.PARSE
    return plugin(func, **hints)


def prompt(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for THINK stage plugins."""

    hints["stage"] = PipelineStage.THINK
    return plugin(func, **hints)


def tool(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for DO stage plugins."""

    hints["stage"] = PipelineStage.DO
    return plugin(func, **hints)


def review(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for REVIEW stage plugins."""

    hints["stage"] = PipelineStage.REVIEW
    return plugin(func, **hints)


def output(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for OUTPUT stage plugins."""

    hints["stage"] = PipelineStage.OUTPUT
    return plugin(func, **hints)


__all__ = [
    "plugin",
    "input",
    "parse",
    "prompt",
    "tool",
    "review",
    "output",
]
