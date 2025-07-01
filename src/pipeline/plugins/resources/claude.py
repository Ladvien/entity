from __future__ import annotations

from typing import Dict

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource
from pipeline.stages import PipelineStage


class ClaudeResource(LLMResource):
    """LLM resource for Anthropic's Claude API.

    Configuration keys:
        - ``api_key``: API token.
        - ``model``: Claude model name.
        - ``base_url``: Base API URL.
        - Additional keys are passed to the API as generation parameters.
    """

    stages = [PipelineStage.PARSE]
    name = "claude"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        """Initialize the helper that manages HTTP requests."""
        super().__init__(config)
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Ensure the configuration contains required fields."""
        return HttpLLMResource(config, require_api_key=True).validate_config()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        """No-op; this resource does not run in a pipeline stage."""
        return None

    async def generate(self, prompt: str) -> str:
        """Call the Claude API with ``prompt`` and return the completion."""
        if not self.http.validate_config().valid:
            raise RuntimeError("Claude resource not properly configured")
        base_url = self.http.base_url or ""
        api_key = self.http.api_key or ""
        model = self.http.model or ""

        url = f"{base_url.rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **self.http.params,
        }
        data = await self.http._post_request(url, payload, headers)
        text = data.get("content", [{}])[0].get("text", "")
        return str(text)

    __call__ = generate
