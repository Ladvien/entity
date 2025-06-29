from __future__ import annotations

<<<<<<< HEAD
from ..plugins import ResourcePlugin
from ..stages import PipelineStage
=======
from typing import Any

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage
>>>>>>> 346eeb378c849154625acfe74df5c293057eca04


class EchoLLMResource(ResourcePlugin):
    """Simple LLM resource that echoes the prompt back."""

    stages = [PipelineStage.PARSE]
    name = "ollama"

    async def _execute_impl(self, context):
        return None

    async def generate(self, prompt: str) -> str:
        return prompt

    __call__ = generate
