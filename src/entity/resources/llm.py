"""Resource wrapper around an Ollama LLM deployment."""

from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class LLMResource:
    """Layer 2 resource that wraps an Ollama LLM."""

    def __init__(self, infrastructure: OllamaInfrastructure | None) -> None:
        """Initialize with the Ollama infrastructure instance."""

        if infrastructure is None:
            raise ResourceInitializationError("OllamaInfrastructure is required")
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    async def generate(self, prompt: str) -> str:
        """Return the model output for a given prompt."""

        return await self.infrastructure.generate(prompt)
