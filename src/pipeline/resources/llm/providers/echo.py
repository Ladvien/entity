from __future__ import annotations

from typing import Dict

from pipeline.validation import ValidationResult

from .base import BaseProvider


class EchoProvider(BaseProvider):
    """Adapter that simply echoes the prompt."""

    name = "echo"

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Echo provider requires no specific configuration."""
        return ValidationResult.success_result()

    async def generate(self, prompt: str) -> str:  # noqa: D401 - simple echo
        return prompt
