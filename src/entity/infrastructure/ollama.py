from __future__ import annotations


class OllamaInfrastructure:
    """Infrastructure primitive for Ollama inference server."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model

    async def setup(self) -> None:  # pragma: no cover - placeholder
        """Ensure the model is available."""
        pass
