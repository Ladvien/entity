from __future__ import annotations

from typing import Dict

import httpx

from entity.resources.interfaces.llm import LLMResource
from entity.core.state import LLMResponse


class OpenAILLMResource(LLMResource):
    """Simple OpenAI LLM provider."""

    name = "openai_provider"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.base_url = self.config.get("base_url", "https://api.openai.com/v1")

    async def generate(self, prompt: str) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", json=data, headers=headers
            )
        return LLMResponse(content=resp.json()["choices"][0]["message"]["content"])


class AnthropicLLMResource(LLMResource):
    """Simple Anthropic LLM provider."""

    name = "anthropic_provider"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "claude-3-opus-20240229")
        self.base_url = self.config.get("base_url", "https://api.anthropic.com")

    async def generate(self, prompt: str) -> LLMResponse:
        headers = {"x-api-key": self.api_key}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v1/messages", json=data, headers=headers
            )
        return LLMResponse(content=resp.json()["content"][0]["text"])
