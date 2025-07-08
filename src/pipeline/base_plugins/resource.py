from __future__ import annotations

from typing import Any, Dict

from ..validation import ValidationResult
from .base import BasePlugin


class ResourcePlugin(BasePlugin):
    async def initialize(self) -> None:
        """Optional async initialization hook."""
        return None

    async def health_check(self) -> bool:
        """Return ``True`` if the resource is healthy."""
        return True

    async def validate_runtime(self) -> "ValidationResult":
        """Validate runtime by performing a health check."""

        try:
            healthy = await self.health_check()
        except Exception as exc:  # pragma: no cover - propagation
            return ValidationResult.error_result(str(exc))
        return (
            ValidationResult.success_result()
            if healthy
            else ValidationResult.error_result("health check failed")
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Return metrics about this resource."""
        return {"status": "healthy"}

    async def __aenter__(self) -> "ResourcePlugin":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()
