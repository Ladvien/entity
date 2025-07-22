from .llm import LLMResource
from .exceptions import ResourceInitializationError


class LLM:
    """Layer 3 wrapper around an LLM resource."""

    def __init__(self, resource: LLMResource | None) -> None:
        if resource is None:
            raise ResourceInitializationError("LLMResource is required")
        self.resource = resource

    async def generate(self, prompt: str) -> str:
        return await self.resource.generate(prompt)
