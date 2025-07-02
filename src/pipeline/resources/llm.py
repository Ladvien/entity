from __future__ import annotations

from abc import ABC, abstractmethod


class LLM(ABC):
    """Abstract interface for language model resources."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Return a completion for ``prompt``."""
