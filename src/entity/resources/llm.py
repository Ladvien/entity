"""Canonical LLM resource."""

from __future__ import annotations

from typing import Any, Dict

from ..core.plugins import ValidationResult

from .base import AgentResource
from .interfaces.llm import LLMResource


class LLM(AgentResource):
    """Simple LLM wrapper."""

    name = "llm"

    def __init__(self, provider: LLMResource, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.provider = provider

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def validate_runtime(self) -> ValidationResult:
        """Validate underlying provider connectivity."""
        if self.provider and hasattr(self.provider, "validate_runtime"):
            result = await self.provider.validate_runtime()
            if not result.success:
                return ValidationResult.error_result(f"provider: {result.message}")
        return ValidationResult.success_result()
