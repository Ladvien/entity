from __future__ import annotations

from typing import Dict

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Adapter for OpenAI chat completion API."""

    name = "openai"
    requires_api_key = True

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("OpenAI provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.http.api_key}"}
        payload = {
            "model": self.http.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.http.params,
        }
        data = await self._post_with_retry(url, payload, headers)
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return str(text)
