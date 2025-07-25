import httpx

from entity.installers.ollama import OllamaInstaller

from .base import BaseInfrastructure


class OllamaInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for communicating with an Ollama server."""

    def __init__(
        self,
        base_url: str,
        model: str,
        version: str | None = None,
        auto_install: bool = True,
    ) -> None:
        """Configure the client base URL, model, and installer settings."""

        super().__init__(version)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.auto_install = auto_install

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

    async def startup(self) -> None:  # pragma: no cover - thin wrapper
        await super().startup()
        self.logger.info("Ollama endpoint %s", self.base_url)

    async def shutdown(self) -> None:  # pragma: no cover - thin wrapper
        await super().shutdown()

    def health_check(self) -> bool:
        """Return ``True`` if the Ollama server responds."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            response.raise_for_status()
            return True
        except Exception as exc:
            if self.auto_install:
                self.logger.debug("Health check failed: %s", exc)
                OllamaInstaller.ensure_installed()
            return False
