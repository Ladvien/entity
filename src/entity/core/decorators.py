from __future__ import annotations

"""Helpers for defining Entity plugins via decorators."""

from typing import Any, Callable, Optional


from .stages import PipelineStage

from .plugin_utils import PluginAutoClassifier
from .plugins import PromptPlugin, ToolPlugin


def plugin(func: Optional[Callable] = None, **hints: Any) -> Callable:
    """Decorator turning ``func`` into a plugin.

    When ``hints`` are omitted the plugin will default to a ``PromptPlugin``
    executed in the ``THINK`` stage.
    """

    def decorator(f: Callable) -> Callable:
        plugin_obj = PluginAutoClassifier.classify(f, hints or None)
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


def prompt_plugin(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for prompt plugins using default stage."""

    hints["plugin_class"] = PromptPlugin
    return plugin(func, **hints)


def tool_plugin(
    func: Optional[Callable] = None, **hints: Any
) -> Callable[[Callable], Callable] | Callable:
    """Decorator for tool plugins using default stage."""

    hints["plugin_class"] = ToolPlugin
    return plugin(func, **hints)


__all__ = [
    "plugin",
    "input",
    "parse",
    "prompt",
    "tool",
    "review",
    "output",
    "prompt_plugin",
    "tool_plugin",
]
