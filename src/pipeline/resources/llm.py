from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pipeline.resources.base import BaseResource


class LLM(ABC):
    """Interface for language model resources."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate text in response to ``prompt``."""

    async def __call__(self, prompt: str) -> str:
        return await self.generate(prompt)


class LLMResource(BaseResource, LLM):
    """Base class for LLM-backed resources."""

    async def generate(self, prompt: str) -> str:
        raise NotImplementedError

    __call__ = generate
