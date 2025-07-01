from __future__ import annotations

from pipeline.resources.llm import LLMResource


class EchoLLMResource(LLMResource):
    """Simple LLM resource that echoes the prompt back."""

    name = "echo"
    aliases = ["llm"]

    async def _execute_impl(self, context):
        return None

    async def generate(self, prompt: str) -> str:
        return prompt

    __call__ = generate
