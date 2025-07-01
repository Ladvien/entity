from __future__ import annotations

from typing import Dict

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource
from pipeline.stages import PipelineStage


class GeminiResource(LLMResource):
    """LLM resource for Google's Gemini API.

    Configuration keys:
        - ``api_key``: Authentication token.
        - ``model``: Model identifier to query.
        - ``base_url``: API endpoint root.
        - Additional keys are forwarded to the request payload.
    """

    stages = [PipelineStage.PARSE]
    name = "gemini"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        """Prepare HTTP helper using ``config``."""
        super().__init__(config)
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Validate that mandatory configuration options are present."""
        return HttpLLMResource(config, require_api_key=True).validate_config()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        """No-op; this resource does not run in a pipeline stage."""
        return None

    async def generate(self, prompt: str) -> str:
        """Generate text for ``prompt`` using the Gemini model."""
        if not self.http.validate_config().valid:
            raise RuntimeError("Gemini resource not properly configured")
        base_url = self.http.base_url or ""
        api_key = self.http.api_key or ""
        model = self.http.model or ""

        url = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}
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
