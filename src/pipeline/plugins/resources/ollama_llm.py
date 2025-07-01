from __future__ import annotations

from typing import Dict

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource


class OllamaLLMResource(LLMResource):
    """LLM resource backed by a running Ollama server.

    The configuration requires ``base_url`` and ``model``. Any additional
    keys are forwarded to the API request payload.
    """

    name = "ollama"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        """Parse connection details from ``config``."""
        super().__init__(config)
        self.http = HttpLLMResource(self.config)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Validate that ``base_url`` and ``model`` are provided."""
        return HttpLLMResource(config).validate_config()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        """No-op; this resource does not run in a pipeline stage."""
        return None

    async def generate(self, prompt: str) -> str:
        """Generate text from ``prompt`` using the Ollama model."""
        if not self.http.validate_config().valid:
            raise RuntimeError("Ollama resource not properly configured")
        base_url = self.http.base_url or ""
        model = self.http.model or ""

        url = f"{base_url.rstrip('/')}/api/generate"
        payload = {"model": model, "prompt": prompt, **self.http.params}
        data = await self.http._post_request(url, payload)
        text = data.get("response", "")
        return str(text)

    __call__ = generate
