from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

from pipeline.state import LLMResponse

from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Adapter for a running Ollama server."""

    name = "ollama"

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        if not self.http.validate_config().valid:
            raise RuntimeError("Ollama provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/api/generate"
        payload = {"model": self.http.model, "prompt": prompt, **self.http.params}
        if functions:
            payload["functions"] = functions
        data = await self._post_with_retry(url, payload)
        text = data.get("response", "")
        return LLMResponse(content=str(text), metadata=data)

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        if not self.http.validate_config().valid:
            raise RuntimeError("Ollama provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.http.model,
            "prompt": prompt,
            "stream": True,
            **self.http.params,
        }
        if functions:
            payload["functions"] = functions

        async for data in self._stream_post_request(url, payload):
            text = data.get("response")
            if text:
                yield str(text)
