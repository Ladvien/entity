from __future__ import annotations

from .base import BaseProvider


class ClaudeProvider(BaseProvider):
    """Adapter for Anthropic's Claude API."""

    name = "claude"
    requires_api_key = True

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("Claude provider not properly configured")

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
        data = await self._post_with_retry(url, payload, headers)
        text = data.get("content", [{}])[0].get("text", "")
        return str(text)
