from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Resource(Protocol):
    """Lightweight interface for runtime resources."""

    async def initialize(self) -> None:
        """Perform optional async initialization."""

    async def health_check(self) -> bool:
        """Return ``True`` if the resource is healthy."""

    def get_metrics(self) -> dict[str, Any]:
        """Return metrics describing the resource."""
