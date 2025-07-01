from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class LLM(ABC):
    """Interface for language model resources."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate text in response to ``prompt``."""

    async def __call__(self, prompt: str) -> str:
        return await self.generate(prompt)


class LLMResource(ResourcePlugin, LLM):
    """Base class for LLM-backed resources."""

    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        raise NotImplementedError

    __call__ = generate
