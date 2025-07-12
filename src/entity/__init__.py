"""Core utilities for the Entity framework."""

from __future__ import annotations

from .core import decorators as _decorators


class _AgentAPI:
    plugin = staticmethod(_decorators.plugin)
    input = staticmethod(_decorators.input)
    parse = staticmethod(_decorators.parse)
    prompt = staticmethod(_decorators.prompt)
    tool = staticmethod(_decorators.tool)
    review = staticmethod(_decorators.review)
    output = staticmethod(_decorators.output)
    prompt_plugin = staticmethod(_decorators.prompt_plugin)
    tool_plugin = staticmethod(_decorators.tool_plugin)


agent = _AgentAPI()

__all__ = ["core", "Agent", "AgentBuilder", "agent"]


def __getattr__(name: str):
    if name == "core":
        from . import core as _core

        return _core
    if name == "Agent":
        from .core.agent import Agent as _Agent

        return _Agent
    if name == "AgentBuilder":
        from .core.builder import _AgentBuilder

        return _AgentBuilder
    raise AttributeError(name)
