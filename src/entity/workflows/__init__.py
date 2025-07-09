from __future__ import annotations

"""Workflow base classes and utilities."""


class Workflow:
    """Base workflow object describing stage order."""

    stages: dict[str, list[str]] = {}


__all__ = ["Workflow"]
