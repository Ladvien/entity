"""Resource wrapper around an LLM infrastructure."""

from typing import Protocol

from entity.resources.exceptions import ResourceInitializationError


class LLMInfrastructure(Protocol):
    async def generate(self, prompt: str) -> str: ...

    def health_check(self) -> bool: ...


class LLMResource:
    """Layer 2 resource that wraps an LLM implementation."""

    def __init__(self, infrastructure: LLMInfrastructure | None) -> None:
        """Initialize with the infrastructure instance."""

        if infrastructure is None:
            raise ResourceInitializationError("LLMInfrastructure is required")
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    async def generate(self, prompt: str) -> str:
        """Return the model output for a given prompt."""

        return await self.infrastructure.generate(prompt)
