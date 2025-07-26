from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMInfrastructure(Protocol):
    """Protocol for infrastructures used by :class:`LLMResource`."""

    async def generate(self, prompt: str) -> str:
        """Generate a completion for ``prompt``."""

    def health_check(self) -> bool:
        """Return ``True`` if the infrastructure is healthy."""
