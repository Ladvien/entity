from __future__ import annotations

import httpx

from .base import BaseInfrastructure


class VLLMInfrastructure(BaseInfrastructure):
    """Simple infrastructure wrapper for a vLLM server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str | None = None,
        version: str | None = None,
    ) -> None:
        super().__init__(version)
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "model": self.model},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def health_check(self) -> bool:
        try:
            httpx.get(f"{self.base_url}/health", timeout=1).raise_for_status()
            return True
        except Exception as exc:  # pragma: no cover - network errors
            self.logger.debug("vLLM health check failed: %s", exc)
            return False
