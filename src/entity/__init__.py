from __future__ import annotations

"""Public package entrypoints."""

# ``Agent`` is re-exported from :mod:`pipeline.agent` so that applications can
# ``from entity import Agent``.
from pipeline.agent import Agent

__all__ = ["Agent"]
