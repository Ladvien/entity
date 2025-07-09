from __future__ import annotations

"""LLM resource that echoes prompts."""
from plugins.builtin.resources.llm_resource import LLMResource


class EchoLLMResource(LLMResource):
    """Simple LLM resource that echoes the prompt back."""

    name = "echo"
    dependencies: list[str] = []

    async def generate(self, prompt: str) -> str:
        return prompt
