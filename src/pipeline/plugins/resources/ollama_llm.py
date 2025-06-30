from __future__ import annotations

from typing import Any, Dict

import httpx

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage
<<<<< codex/update-ollama_llm-entries-and-example
from pipeline.state import LLMResponse


class OllamaLLMResource(ResourcePlugin):
    """LLM resource that communicates with a local Ollama server."""
======


class OllamaLLMResource(ResourcePlugin):
    """LLM resource backed by a running Ollama server."""
>>>> main

    stages = [PipelineStage.PARSE]
    name = "ollama"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
<<<<< codex/update-ollama_llm-entries-and-example
        self.base_url: str = str(self.config.get("base_url", "http://localhost:11434"))
        self.model: str = str(self.config.get("model", ""))
        self.temperature: float = float(self.config.get("temperature", 0.7))
======
        self.base_url: str | None = self.config.get("base_url")
        self.model: str | None = self.config.get("model")
        self.params: Dict[str, Any] = {
            k: v for k, v in self.config.items() if k not in {"base_url", "model"}
        }
          
>>>>> main

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("base_url"):
            return ValidationResult.error_result("'base_url' is required")
        if not config.get("model"):
            return ValidationResult.error_result("'model' is required")
        return ValidationResult.success_result()

<<<<< codex/update-ollama_llm-entries-and-example
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
======
    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        if not self.base_url or not self.model:
            raise RuntimeError("Ollama resource not properly configured")

        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {"model": self.model, "prompt": prompt, **self.params}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        text = data.get("response", "")
        return str(text)
>>>>> main

    __call__ = generate
