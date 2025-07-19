from __future__ import annotations

from typing import Dict

from entity.core.plugins import InfrastructurePlugin, ValidationResult


class EchoLLMBackend(InfrastructurePlugin):
    """Simple backend that echoes prompts."""

    name = "echo_llm_backend"
    infrastructure_type = "llm_provider"
    resource_category = "llm"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})

    async def generate(self, prompt: str) -> str:
        return prompt

    async def validate_runtime(self) -> ValidationResult:
        return ValidationResult.success_result()
