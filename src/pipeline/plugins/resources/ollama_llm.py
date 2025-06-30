from __future__ import annotations

from typing import Any, Dict

import httpx

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage


class OllamaLLMResource(ResourcePlugin):
    """LLM resource that sends prompts to an Ollama server."""

    stages = [PipelineStage.PARSE]
    name = "ollama"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.base_url: str = self.config.get("base_url", "http://localhost:11434")
        self.model: str = self.config.get("model", "llama3")
        self.timeout: int = int(self.config.get("timeout", 30))

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("base_url"):
            return ValidationResult.error_result("'base_url' is required")
        if not config.get("model"):
            return ValidationResult.error_result("'model' is required")
        return ValidationResult.success_result()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        data = response.json()
        return str(data.get("response", ""))

    __call__ = generate
