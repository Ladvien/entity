"""Canonical LLM resource."""

from __future__ import annotations

from typing import Any, Dict

from ..core.plugins import ValidationResult
from entity.config.models import LLMConfig
from pydantic import ValidationError

from .base import AgentResource
from .interfaces.llm import LLMResource


class LLM(AgentResource):
    """Simple LLM wrapper."""

    name = "llm"
    dependencies = ["llm_provider"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.provider: LLMResource | None = None

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            LLMConfig.parse_obj(config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def validate_runtime(self) -> ValidationResult:
        """Validate underlying provider connectivity."""
        if self.provider and hasattr(self.provider, "validate_runtime"):
            result = await self.provider.validate_runtime()
            if not result.success:
                return ValidationResult.error_result(f"provider: {result.message}")
        return ValidationResult.success_result()
