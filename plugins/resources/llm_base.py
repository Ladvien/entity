from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from pipeline.state import LLMResponse


class LLM(ABC):
    """Abstract interface for language model resources."""

    @abstractmethod
    async def generate(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> "LLMResponse":
        """Return text in response to ``prompt``."""

    async def __call__(self, prompt: str) -> str:
        return (await self.generate(prompt)).content

    async def stream(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError
