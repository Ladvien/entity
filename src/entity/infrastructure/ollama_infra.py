import time
import httpx

from entity.setup.ollama_installer import OllamaInstaller

from .base import BaseInfrastructure


class OllamaInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for communicating with an Ollama server."""

    def __init__(
        self,
        base_url: str,
        model: str,
        version: str | None = None,
    ) -> None:
        """Configure the client base URL, model, and installer settings."""

        super().__init__(version)
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated text."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def startup(self) -> None:
        await super().startup()
        self.logger.info("Ollama endpoint %s", self.base_url)

    async def shutdown(self) -> None:
        await super().shutdown()

    def health_check(self) -> bool:
        """Return ``True`` if the Ollama server responds."""

        for attempt in range(3):
            try:
                response = httpx.get(f"{self.base_url}/api/tags", timeout=2)
                response.raise_for_status()
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
        return False
