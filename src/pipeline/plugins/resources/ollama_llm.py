from __future__ import annotations

from typing import Dict

from pipeline.base_plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource


class OllamaLLMResource(LLMResource):
    """LLM resource backed by a running Ollama server.

    Uses **Structured LLM Access (22)** so any stage can generate text while the
    framework automatically tracks token usage.
    """

    name = "ollama"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.http = HttpLLMResource(self.config)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(config).validate_config()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("Ollama resource not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/api/generate"
        payload = {"model": self.http.model, "prompt": prompt, **self.http.params}
        data = await self.http._post_request(url, payload)
        text = data.get("response", "")
        return str(text)

    __call__ = generate
