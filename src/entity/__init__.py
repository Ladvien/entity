from __future__ import annotations

"""Public package entrypoints."""

# ``Agent`` is re-exported from :mod:`entity.agent` so that applications can
# ``from entity import Agent``.
from .agent import Agent

__all__ = ["Agent"]
