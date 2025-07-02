from __future__ import annotations

from typing import Dict

import httpx

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.llm_resource import LLMResource


class OpenAIResource(LLMResource):
    """LLM resource for OpenAI's chat completion API."""

    name = "openai"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.api_key: str | None = self.config.get("api_key")
        self.model: str | None = self.config.get("model")
        self.base_url: str | None = self.config.get("base_url")
        self.params = self.extract_params(self.config, ["api_key", "model", "base_url"])

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return cls.validate_required_fields(config, ["api_key", "model", "base_url"])

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        if not self.api_key or not self.model or not self.base_url:
            raise RuntimeError("OpenAI resource not properly configured")

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.params,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        data = response.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return str(text)
