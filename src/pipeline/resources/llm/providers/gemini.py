from __future__ import annotations

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Adapter for Google's Gemini API."""

    name = "gemini"
    requires_api_key = True

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("Gemini provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/v1beta/models/{self.http.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.http.api_key}
        payload = {"contents": [{"parts": [{"text": prompt}]}], **self.http.params}
        data = await self._post_with_retry(url, payload, headers, params)
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return str(text)
