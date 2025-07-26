from __future__ import annotations

import httpx

from .base import BaseInfrastructure


class VLLMInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for a vLLM server."""

    def __init__(self, base_url: str, model: str, version: str | None = None) -> None:
        super().__init__(version)
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={"model": self.model, "prompt": prompt},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", data.get("text", ""))

    def health_check(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2)
            response.raise_for_status()
            return True
        except Exception:
            return False
