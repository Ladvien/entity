from __future__ import annotations

from typing import Any, Dict

import httpx

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage
from pipeline.state import LLMResponse


class OllamaLLMResource(ResourcePlugin):
    """LLM resource that communicates with a local Ollama server."""

    stages = [PipelineStage.PARSE]
    name = "ollama"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.base_url: str = str(self.config.get("base_url", "http://localhost:11434"))
        self.model: str = str(self.config.get("model", ""))
        self.temperature: float = float(self.config.get("temperature", 0.7))

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("base_url"):
            return ValidationResult.error_result("'base_url' is required")
        if not config.get("model"):
            return ValidationResult.error_result("'model' is required")
        return ValidationResult.success_result()

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> LLMResponse:  # pragma: no cover - network
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate", json=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        content = data.get("response") if isinstance(data, dict) else str(data)
        return LLMResponse(content=str(content))

    __call__ = generate
