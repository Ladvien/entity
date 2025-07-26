import time
import httpx

from .base import BaseInfrastructure
from entity.setup.vllm_installer import VLLMInstaller


class VLLMInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for a local vLLM service."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str | None = None,
        version: str | None = None,
        auto_install: bool = True,
    ) -> None:
        super().__init__(version)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.auto_install = auto_install

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "model": self.model},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("text", "")

    def health_check(self) -> bool:
        for attempt in range(3):
            try:
                resp = httpx.get(f"{self.base_url}/health", timeout=2)
                resp.raise_for_status()
                self.logger.debug(
                    "Health check succeeded for %s on attempt %s",
                    self.base_url,
                    attempt + 1,
                )
                return True
            except Exception as exc:
                self.logger.debug(
                    "Health check attempt %s failed for %s: %s",
                    attempt + 1,
                    self.base_url,
                    exc,
                )
                time.sleep(1)

        self.logger.warning("Health check failed for %s", self.base_url)
        if self.auto_install:
            self.logger.debug("Attempting automatic vLLM install")
            VLLMInstaller.ensure_vllm_available(self.model)
        return False
