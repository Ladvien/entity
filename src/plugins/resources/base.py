from __future__ import annotations

"""Common base implementation for asynchronous resources."""
from typing import TYPE_CHECKING, Any, Dict, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from registry import ClassRegistry

from pipeline.logging import get_logger
from pipeline.validation import ValidationResult


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

    async def __aenter__(self) -> "BaseResource":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()

    # ------------------------------------------------------------------
    # Validation helpers matching BasePlugin API
    # ------------------------------------------------------------------
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return ValidationResult.success_result()

    @classmethod
    def validate_dependencies(cls, registry: "ClassRegistry") -> ValidationResult:
        return ValidationResult.success_result()


__all__ = ["Resource", "BaseResource"]
