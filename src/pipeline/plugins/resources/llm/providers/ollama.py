from __future__ import annotations

from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Adapter for a running Ollama server."""

    name = "ollama"

    async def generate(self, prompt: str) -> str:
        if not self.http.validate_config().valid:
            raise RuntimeError("Ollama provider not properly configured")

        url = f"{self.http.base_url.rstrip('/')}/api/generate"
        payload = {"model": self.http.model, "prompt": prompt, **self.http.params}
        data = await self._post_with_retry(url, payload)
        text = data.get("response", "")
        return str(text)
