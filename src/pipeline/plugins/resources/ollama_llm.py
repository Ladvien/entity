from __future__ import annotations

from typing import Dict

import httpx

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.llm_resource import LLMResource


class OllamaLLMResource(LLMResource):
    """LLM resource backed by a running Ollama server.

    Uses **Structured LLM Access (22)** so any stage can generate text while the
    framework automatically tracks token usage.
    """

    name = "ollama"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.base_url: str | None = self.config.get("base_url")
        self.model: str | None = self.config.get("model")
        self.params = self.extract_params(self.config, ["base_url", "model"])

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return cls.validate_required_fields(config, ["base_url", "model"])

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        if not self.base_url or not self.model:
            raise RuntimeError("Ollama resource not properly configured")

        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {"model": self.model, "prompt": prompt, **self.params}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        text = data.get("response", "")
        return str(text)
