import httpx


class OllamaInfrastructure:
    """Layer 1 infrastructure for communicating with an Ollama server."""

    def __init__(self, base_url: str, model: str) -> None:
        """Configure the client base URL and model."""

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

    def health_check(self) -> bool:
        """Return ``True`` if the Ollama server responds."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            response.raise_for_status()
            return True
        except Exception:
            return False
