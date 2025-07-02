from __future__ import annotations

from typing import Any, Dict, List

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.resources import LLM
from pipeline.stages import PipelineStage


class LLMResource(ResourcePlugin, LLM):
    """Base class for language model resources."""

    stages = [PipelineStage.PARSE]
    name = "llm"

    async def _execute_impl(self, context) -> None:
        return None

    async def generate(self, prompt: str) -> str:
        """Return a completion for ``prompt``."""

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
