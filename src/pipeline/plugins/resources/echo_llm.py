from __future__ import annotations

from pipeline.plugins.resources.llm_resource import LLMResource


class EchoLLMResource(LLMResource):
    """Simple LLM resource that echoes the prompt back."""

    name = "echo"

    async def _execute_impl(self, context):
        return None

    async def generate(self, prompt: str) -> str:
        return prompt
