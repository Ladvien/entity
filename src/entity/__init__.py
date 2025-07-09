"""Core utilities for the Entity framework."""

from __future__ import annotations

__all__ = ["core", "Agent", "AgentBuilder"]


def __getattr__(name: str):
    if name == "core":
        from . import core as _core

        return _core
    if name == "Agent":
        from .core.agent import Agent as _Agent

        return _Agent
    if name == "AgentBuilder":
        from .core.builder import AgentBuilder as _AgentBuilder

        return _AgentBuilder
    raise AttributeError(name)
