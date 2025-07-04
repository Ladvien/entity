from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

from pipeline.state import LLMResponse
from pipeline.validation import ValidationResult

from .base import BaseResource
from .llm_base import LLM


class LLMResource(BaseResource, LLM):
    """Base class for language model resources."""

    name = "llm"

    async def generate(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> "LLMResponse":
        """Return a completion for ``prompt``."""

        raise NotImplementedError

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Yield tokens for ``prompt`` using server-sent events."""

        raise NotImplementedError

    __call__ = generate

    @staticmethod
    def validate_required_fields(config: Dict, fields: List[str]) -> "ValidationResult":
        """Verify that all ``fields`` exist in ``config``."""

        missing = [field for field in fields if not config.get(field)]
        if missing:
            joined = ", ".join(missing)
            return ValidationResult.error_result(f"missing required fields: {joined}")
        return ValidationResult.success_result()

    @staticmethod
    def extract_params(config: Dict, required: List[str]) -> Dict[str, Any]:
        """Return all items in ``config`` except those in ``required``."""

        return {k: v for k, v in config.items() if k not in required}
