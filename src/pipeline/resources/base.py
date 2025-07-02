from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

from pipeline.logging import get_logger


@runtime_checkable
class Resource(Protocol):
    """Lightweight interface for runtime resources."""

    async def initialize(self) -> None:
        """Perform optional async initialization."""

    async def shutdown(self) -> None:
        """Perform optional cleanup."""

    async def health_check(self) -> bool:
        """Return ``True`` if the resource is healthy."""

    def get_metrics(self) -> dict[str, Any]:
        """Return metrics describing the resource."""


class BaseResource:
    """Convenient base class implementing :class:`Resource`."""

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    async def initialize(self) -> None:  # pragma: no cover - optional
        return None

    async def shutdown(self) -> None:  # pragma: no cover - optional
        return None

    async def health_check(self) -> bool:
        return True

    def get_metrics(self) -> dict[str, Any]:
        return {"status": "healthy"}
