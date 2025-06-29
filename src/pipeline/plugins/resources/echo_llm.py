from __future__ import annotations

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class EchoLLMResource(ResourcePlugin):
    """Simple LLM resource that echoes the prompt back."""

    stages = [PipelineStage.PARSE]
    name = "ollama"

    async def _execute_impl(self, context):
        return None

    async def generate(self, prompt: str) -> str:
        return prompt

    __call__ = generate
