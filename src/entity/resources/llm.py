"""Resource wrapper around an LLM infrastructure."""

from entity.resources.exceptions import ResourceInitializationError
from .llm_protocol import LLMInfrastructure


class LLMResource:
    """Layer 2 resource that wraps an LLM infrastructure."""

    def __init__(self, infrastructure: LLMInfrastructure | None) -> None:
        """Initialize with the infrastructure instance."""

        if infrastructure is None:
            raise ResourceInitializationError("LLM infrastructure is required")
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    async def generate(self, prompt: str) -> str:
        """Return the model output for a given prompt."""

        return await self.infrastructure.generate(prompt)
