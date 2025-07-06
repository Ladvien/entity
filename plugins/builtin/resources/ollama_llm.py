from __future__ import annotations

"""LLM resource backed by Ollama."""
from typing import Dict

from plugins.builtin.resources.http_llm_resource import HttpLLMResource
from plugins.builtin.resources.llm_resource import LLMResource

from pipeline.exceptions import ResourceError
from pipeline.validation import ValidationResult


class OllamaLLMResource(LLMResource):
    """LLM resource backed by a running Ollama server.

    Uses **Structured LLM Access (22)** so any stage can generate text while the
    framework automatically tracks token usage.
    """

    name = "ollama"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.http = HttpLLMResource(self.config)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(config).validate_config()

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise ResourceError("Ollama resource not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/api/generate"
        payload = {"model": self.http.model, "prompt": prompt, **self.http.params}
        data = await self.http._post_request(url, payload)
        text = data.get("response", "")
        return str(text)
