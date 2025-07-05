from __future__ import annotations

"""Shared resource lifecycle protocol."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResourceLifecycle(Protocol):
    """Async context manager interface for resources."""

    async def __aenter__(self) -> Any:
        """Enter the resource context."""
        ...

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Cleanup the resource on exit."""
        ...
