from __future__ import annotations

"""LLM resource for OpenAI's API."""
from typing import Any, AsyncIterator, Dict, List

from pipeline.exceptions import ResourceError
from pipeline.state import LLMResponse

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Adapter for OpenAI chat completion API."""

    name = "openai"
    requires_api_key = True

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        if not self.http.validate_config().valid:
            raise ResourceError("OpenAI provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.http.api_key}"}
        payload = {
            "model": self.http.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.http.params,
        }
        if functions:
            payload["functions"] = functions
        data = await self._post_with_retry(url, payload, headers)
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return LLMResponse(
            content=str(text),
            metadata=data,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        if not self.http.validate_config().valid:
            raise ResourceError("OpenAI provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.http.api_key}"}
        payload = {
            "model": self.http.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **self.http.params,
        }
        if functions:
            payload["functions"] = functions

        async for data in self._stream_post_request(url, payload, headers):
            delta = data.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")
            if content:
                yield str(content)
