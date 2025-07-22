"""Layer 3 canonical LLM resource."""

from __future__ import annotations

from .interfaces import LLMResource, ResourceInitializationError


class LLM:
    """Unified interface to a language model."""

    def __init__(self, llm_resource: LLMResource) -> None:
        if llm_resource is None:
            raise ResourceInitializationError("LLMResource required")
        self.llm_resource = llm_resource

    async def setup(self) -> None:  # pragma: no cover - placeholder
        """Ensure model availability."""
        pass
