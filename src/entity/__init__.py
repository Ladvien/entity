from __future__ import annotations

"""Public package entrypoints."""

# ``Agent`` is re-exported from :mod:`pipeline.agent` so that applications can
# ``from entity import Agent``. The implementation lives in ``pipeline.agent``
# and is considered the canonical API.
from pipeline.agent import Agent

__all__ = ["Agent"]
