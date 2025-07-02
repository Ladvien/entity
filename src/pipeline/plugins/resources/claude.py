from __future__ import annotations

from typing import Dict

from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.plugins.resources.llm_resource import LLMResource
from pipeline.validation import ValidationResult


class ClaudeResource(LLMResource):
    """LLM resource for Anthropic's Claude API."""

    name = "claude"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(config, require_api_key=True).validate_config()

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("Claude resource not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": self.http.api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": self.http.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.http.params,
        }
        data = await self.http._post_request(url, payload, headers)
        text = data.get("content", [{}])[0].get("text", "")
        return str(text)

    __call__ = generate
