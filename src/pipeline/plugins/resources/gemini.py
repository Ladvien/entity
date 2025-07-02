from __future__ import annotations

from typing import Dict

<<<<<<< HEAD
from pipeline.base_plugins import ValidationResult
from pipeline.plugins.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm import LLMResource
=======
import httpx

from pipeline.plugins import ValidationResult
from pipeline.plugins.resources.llm_resource import LLMResource
>>>>>>> 5254d8c570961a7008f230d11e4766175159d40a
from pipeline.stages import PipelineStage


class GeminiResource(LLMResource):
    """LLM resource for Google's Gemini API."""

    stages = [PipelineStage.PARSE]
    name = "gemini"
    aliases = ["llm"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
<<<<<<< HEAD
        self.http = HttpLLMResource(self.config, require_api_key=True)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(config, require_api_key=True).validate_config()
=======
        self.api_key: str | None = self.config.get("api_key")
        self.model: str | None = self.config.get("model")
        self.base_url: str | None = self.config.get("base_url")
        self.params = self.extract_params(self.config, ["api_key", "model", "base_url"])

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return cls.validate_required_fields(config, ["api_key", "model", "base_url"])
>>>>>>> 5254d8c570961a7008f230d11e4766175159d40a

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

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
