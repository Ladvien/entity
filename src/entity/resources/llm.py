"""Resource wrapper around an Ollama LLM deployment."""

from entity.infrastructure.ollama_infra import OllamaInfrastructure


class LLMResource:
    """Layer 2 resource that wraps an Ollama LLM."""

    def __init__(self, infrastructure: OllamaInfrastructure) -> None:
        """Initialize with the Ollama infrastructure instance."""

        self.infrastructure = infrastructure

    async def generate(self, prompt: str) -> str:
        """Return the model output for a given prompt."""

        return await self.infrastructure.generate(prompt)
