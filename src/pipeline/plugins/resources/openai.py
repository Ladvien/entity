from __future__ import annotations

from typing import Dict

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource


class OpenAIResource(LLMResource):
    """Interface to OpenAI's chat completion API.

    Configuration keys:
        - ``api_key``: API token for authentication.
        - ``model``: Model name to invoke.
        - ``base_url``: Endpoint for the OpenAI service.
        - Any additional keys are passed directly to the API request.
    """

    name = "openai"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        """Store API connection details from ``config``."""
        super().__init__(config)
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Validate that required configuration fields are present."""
        return HttpLLMResource(config, require_api_key=True).validate_config()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        """No-op; this resource does not run in a pipeline stage."""
        return None

    async def generate(self, prompt: str) -> str:
        """Call the OpenAI API with ``prompt`` and return the response text."""
        if not self.http.validate_config().valid:
            raise RuntimeError("OpenAI resource not properly configured")
        base_url = self.http.base_url or ""
        api_key = self.http.api_key or ""
        model = self.http.model or ""

        url = f"{base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **self.http.params,
        }
        data = await self.http._post_request(url, payload, headers)
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return str(text)

    __call__ = generate
