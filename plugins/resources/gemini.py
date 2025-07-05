from __future__ import annotations

"""Adapter for Google's Gemini API."""
from typing import Dict

from pipeline.validation import ValidationResult
from plugins.resources.http_llm_resource import HttpLLMResource
from plugins.resources.llm_resource import LLMResource


class GeminiResource(LLMResource):
    """LLM resource for Google's Gemini API."""

    name = "gemini"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(config, require_api_key=True).validate_config()

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("Gemini resource not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1beta/models/{self.http.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.http.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            **self.http.params,
        }
        data = await self.http._post_request(url, payload, headers, params)
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return str(text)

    __call__ = generate
