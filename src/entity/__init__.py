from __future__ import annotations

# Export the high level :class:`Agent` class so users can simply do
# ``from entity import Agent``.  We re-export the implementation from the
# :mod:`pipeline` package to keep the import path stable.
from pipeline.agent import Agent

__all__ = ["Agent"]
