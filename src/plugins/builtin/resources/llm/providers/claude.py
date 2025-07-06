from __future__ import annotations

"""Adapter for Anthropic Claude API."""
from typing import Any, AsyncIterator, Dict, List

from pipeline.exceptions import ResourceError
from pipeline.state import LLMResponse

from .base import BaseProvider


class ClaudeProvider(BaseProvider):
    """Adapter for Anthropic's Claude API."""

    name = "claude"
    requires_api_key = True

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        if not self.http.validate_config().success:
            raise ResourceError("Claude provider not properly configured")

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
        if functions:
            payload["functions"] = functions
        data = await self._post_with_retry(url, payload, headers)
        text = data.get("content", [{}])[0].get("text", "")
        return LLMResponse(content=str(text), metadata=data)

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        if not self.http.validate_config().success:
            raise ResourceError("Claude provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": self.http.api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": self.http.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **self.http.params,
        }
        if functions:
            payload["functions"] = functions

        async for data in self._stream_post_request(url, payload, headers):
            text = data.get("content", [{}])[0].get("text")
            if text:
                yield str(text)
