from __future__ import annotations

"""LLM resource that echoes prompts."""
from plugins.resources.llm_resource import LLMResource


class EchoLLMResource(LLMResource):
    """Simple LLM resource that echoes the prompt back."""

    name = "echo"

    async def generate(self, prompt: str) -> str:
        return prompt
