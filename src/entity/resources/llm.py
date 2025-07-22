from ..infrastructure.ollama_infra import OllamaInfrastructure


class LLMResource:
    """Layer 2 resource that wraps an Ollama LLM."""

    def __init__(self, infrastructure: OllamaInfrastructure) -> None:
        self.infrastructure = infrastructure

    async def generate(self, prompt: str) -> str:
        return await self.infrastructure.generate(prompt)
