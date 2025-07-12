from __future__ import annotations

from typing import Dict

import httpx

from entity.core.state import LLMResponse
from entity.resources.interfaces.llm import LLMResource


class OllamaLLMResource(LLMResource):
    """LLM provider using a local Ollama server."""

    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.model = self.config.get("model", "llama3")
        self.base_url = self.config.get("base_url", "http://localhost:11434")

    async def generate(self, prompt: str) -> LLMResponse:
        data = {"model": self.model, "prompt": prompt}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=data)
        return LLMResponse(content=resp.json().get("response", ""))
