from __future__ import annotations

"""Adapter for Google's Gemini API."""
from typing import Any, AsyncIterator, Dict, List

from pipeline.exceptions import ResourceError
from pipeline.state import LLMResponse

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Adapter for Google's Gemini API."""

    name = "gemini"
    requires_api_key = True

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        if not self.http.validate_config().valid:
            raise ResourceError("Gemini provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1beta/models/{self.http.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.http.api_key}
        payload = {"contents": [{"parts": [{"text": prompt}]}], **self.http.params}
        if functions:
            payload["functions"] = functions
        data = await self._post_with_retry(url, payload, headers, params)
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return LLMResponse(content=str(text), metadata=data)

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        if not self.http.validate_config().valid:
            raise ResourceError("Gemini provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1beta/models/{self.http.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.http.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "stream": True,
            **self.http.params,
        }
        if functions:
            payload["functions"] = functions

        async for data in self._stream_post_request(url, payload, headers, params):
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text")
            )
            if text:
                yield str(text)
