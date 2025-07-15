from __future__ import annotations

from html import escape
from typing import Any, Dict

from entity.core.plugins import ResourcePlugin, ValidationResult
from entity.core.state import LLMResponse


class LLMResource(ResourcePlugin):
    """Base class for simple LLM resources."""

    name = "llm_provider"
    infrastructure_dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def generate(self, prompt: str) -> LLMResponse:
        """Return an ``LLMResponse`` for ``prompt``."""
        return LLMResponse(content=prompt)

    async def call_llm(self, prompt: str, *, sanitize: bool = False) -> str:
        """Helper used in tests to call ``generate`` with optional sanitization."""
        if sanitize:
            prompt = escape(prompt)
        result = await self.generate(prompt)
        return getattr(result, "content", str(result))

    async def validate_runtime(self) -> ValidationResult:
        """Validate that the LLM backend is reachable."""
        try:
            await self.generate("ping")
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()
