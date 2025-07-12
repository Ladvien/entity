"""Canonical resource types."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.plugins import ResourcePlugin


class AgentResource(ResourcePlugin):
    """Layer 3 building block depending only on infrastructure resources."""


from .llm import LLM
from .memory import Memory
from .storage import Storage


@dataclass
class StandardResources:
    """Typed view of canonical resources."""

    llm: LLM
    memory: Memory
    storage: Storage
