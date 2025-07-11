from __future__ import annotations

from typing import Any, Dict

from entity.core.state import LLMResponse

from .llm_resource import LLMResource


class EchoLLMResource(LLMResource):
    """LLM that simply echoes the prompt."""

    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def generate(self, prompt: str) -> LLMResponse:
        return LLMResponse(content=prompt)
