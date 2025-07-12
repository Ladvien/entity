from __future__ import annotations

"""Canonical resource types."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.plugins import ResourcePlugin


class AgentResource(ResourcePlugin):
    """Layer 3 building block depending only on infrastructure resources."""


if TYPE_CHECKING:  # pragma: no cover
    from .memory import Memory
    from .llm import LLM
    from .storage import Storage


@dataclass
class StandardResources:
    """Typed view of canonical resources."""

    llm: "LLM"
    memory: "Memory"
    storage: "Storage"
