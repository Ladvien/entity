from __future__ import annotations

from abc import ABC, abstractmethod
<<<<<<< HEAD
from typing import Any

from pipeline.resources.base import BaseResource
=======
>>>>>>> cf2f639e2825c3c5653576aef6ed05524944e947


class LLM(ABC):
    """Abstract interface for language model resources."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
<<<<<<< HEAD
        """Generate text in response to ``prompt``."""

    async def __call__(self, prompt: str) -> str:
        return await self.generate(prompt)


class LLMResource(BaseResource, LLM):
    """Base class for LLM-backed resources."""

    async def generate(self, prompt: str) -> str:
        raise NotImplementedError

    __call__ = generate
=======
        """Return a completion for ``prompt``."""
>>>>>>> cf2f639e2825c3c5653576aef6ed05524944e947
