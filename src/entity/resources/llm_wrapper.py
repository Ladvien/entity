from entity.resources.exceptions import ResourceInitializationError
from entity.resources.llm import LLMResource


class LLM:
    """Layer 3 wrapper around an LLM resource."""

    def __init__(self, resource: LLMResource | None) -> None:
        """Wrap the provided :class:`LLMResource`."""

        if resource is None:
            raise ResourceInitializationError("LLMResource is required")
        self.resource = resource

    def health_check(self) -> bool:
        """Return ``True`` if the underlying resource is healthy."""

        return self.resource.health_check_sync()

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for compatibility."""
        return self.health_check()

    async def generate(self, prompt: str) -> str:
        """Generate a completion using the underlying resource."""

        return await self.resource.generate(prompt)
