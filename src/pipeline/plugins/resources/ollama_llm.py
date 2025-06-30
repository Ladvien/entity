from __future__ import annotations

from typing import Any, Dict

import httpx

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage


class OllamaLLMResource(ResourcePlugin):
<<<<<< codex/create-tests-for-ollamallmresource
    """LLM resource that sends prompts to an Ollama server."""
======
    """LLM resource backed by a running Ollama server."""
>>>>>> main

    stages = [PipelineStage.PARSE]
    name = "ollama"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
<<<<<< codex/create-tests-for-ollamallmresource
        self.base_url: str = self.config.get("base_url", "http://localhost:11434")
        self.model: str = self.config.get("model", "llama3")
        self.timeout: int = int(self.config.get("timeout", 30))
======
        self.base_url: str | None = self.config.get("base_url")
        self.model: str | None = self.config.get("model")
        self.params: Dict[str, Any] = {
            k: v for k, v in self.config.items() if k not in {"base_url", "model"}
        }
>>>>>> main

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
<<<<<< codex/create-tests-for-ollamallmresource
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        data = response.json()
        return str(data.get("response", ""))
======
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
>>>>>> main

    __call__ = generate
