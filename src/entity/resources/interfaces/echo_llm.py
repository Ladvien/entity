from __future__ import annotations

from typing import Dict

from entity.core.state import LLMResponse

from entity.resources.interfaces.llm import LLMResource


class EchoLLMResource(LLMResource):
    """LLM that simply echoes the prompt."""

    infrastructure_dependencies = ["echo_llm_backend"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def generate(self, prompt: str) -> LLMResponse:
        return LLMResponse(content=prompt)
