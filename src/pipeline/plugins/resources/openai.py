from __future__ import annotations

from typing import Dict

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource


class OpenAIResource(LLMResource):
    """LLM resource for OpenAI's chat completion API."""

    name = "openai"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(config, require_api_key=True).validate_config()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("OpenAI resource not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.http.api_key}"}
        payload = {
            "model": self.http.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.http.params,
        }
        data = await self.http._post_request(url, payload, headers)
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return str(text)
