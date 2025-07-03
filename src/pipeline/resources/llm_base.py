from __future__ import annotations

from abc import ABC, abstractmethod


class LLM(ABC):
    """Abstract interface for language model resources."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Return text in response to ``prompt``."""

    async def __call__(self, prompt: str) -> str:
        return await self.generate(prompt)
