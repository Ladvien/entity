"""Resource wrapper around an LLM infrastructure."""
<<<<<<< HEAD

<<<<<<< HEAD
from entity.infrastructure.base import BaseInfrastructure
=======
>>>>>>> pr-1947
=======

from typing import Protocol

>>>>>>> pr-1954
from entity.resources.exceptions import ResourceInitializationError
from .llm_protocol import LLMInfrastructure


<<<<<<< HEAD
class LLMResource:
    """Layer 2 resource that wraps an LLM infrastructure."""

<<<<<<< HEAD
    def __init__(self, infrastructure: BaseInfrastructure | None) -> None:
=======
    def __init__(self, infrastructure: LLMInfrastructure | None) -> None:
>>>>>>> pr-1947
        """Initialize with the infrastructure instance."""

        if infrastructure is None:
            raise ResourceInitializationError("LLM infrastructure is required")
=======
class LLMInfrastructure(Protocol):
    async def generate(self, prompt: str) -> str: ...

    def health_check(self) -> bool: ...


class LLMResource:
    """Layer 2 resource that wraps an LLM implementation."""

    def __init__(self, infrastructure: LLMInfrastructure | None) -> None:
        """Initialize with the infrastructure instance."""

        if infrastructure is None:
            raise ResourceInitializationError("LLMInfrastructure is required")
>>>>>>> pr-1954
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    async def generate(self, prompt: str) -> str:
        """Return the model output for a given prompt."""

        return await self.infrastructure.generate(prompt)
