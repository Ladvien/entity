"""Core utilities for the Entity framework."""

from __future__ import annotations

__all__ = ["core"]


def __getattr__(name: str):
    if name == "core":
        from . import core as _core

        return _core
    raise AttributeError(name)
