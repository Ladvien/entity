from __future__ import annotations

"""Adapter that echoes the prompt back."""
from typing import Any, AsyncIterator, Dict, List

from pipeline.state import LLMResponse
from pipeline.validation import ValidationResult

from .base import BaseProvider


class EchoProvider(BaseProvider):
    """Adapter that simply echoes the prompt."""

    name = "echo"

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Echo provider requires no specific configuration."""
        return ValidationResult.success_result()

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:  # noqa: D401 - simple echo
        return LLMResponse(content=prompt)

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        yield prompt
