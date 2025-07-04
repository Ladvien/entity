from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Type

from pipeline.plugins import ValidationResult
from pipeline.resources.llm_resource import LLMResource
from pipeline.state import LLMResponse

from .providers import (
    BedrockProvider,
    ClaudeProvider,
    EchoProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)


class UnifiedLLMResource(LLMResource):
    """LLM resource selecting a provider at runtime."""

    name = "llm"

    PROVIDERS: Dict[str, Type[LLMResource]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "bedrock": BedrockProvider,
        "echo": EchoProvider,
    }

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        provider_name = str(self.config.get("provider", "echo")).lower()
        provider_cls = self.PROVIDERS.get(provider_name, EchoProvider)
        clean_config = {
            k: v
            for k, v in self.config.items()
            if k not in {"provider", "fallback", "model_map"}
        }
        result = provider_cls.validate_config(clean_config)
        if not result.success:
            raise ValueError(result.error_message)
        self._provider = provider_cls(clean_config)
        self._model_map: Dict[str, str] = self.config.get("model_map", {})

        fallback_name = str(self.config.get("fallback", "echo")).lower()
        if fallback_name == provider_name:
            self._fallback = None
        else:
            fallback_cls = self.PROVIDERS.get(fallback_name, EchoProvider)
            fb_result = fallback_cls.validate_config(clean_config)
            if not fb_result.success:
                raise ValueError(fb_result.error_message)
            self._fallback = fallback_cls(clean_config)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        provider_name = str(config.get("provider", "echo")).lower()
        provider_cls = cls.PROVIDERS.get(provider_name)
        if not provider_cls:
            return ValidationResult.error_result(
                f"Unknown LLM provider '{provider_name}'"
            )
        return provider_cls.validate_config(config)

    def _select_model(self, prompt: str) -> None:
        for key, model in self._model_map.items():
            if key.lower() in prompt.lower():
                if hasattr(self._provider, "http"):
                    self._provider.http.model = model
                break

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        self._select_model(prompt)
        try:
            return await self._provider.generate(prompt, functions)
        except Exception:
            if self._fallback is not None:
                return await self._fallback.generate(prompt, functions)
            raise

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        self._select_model(prompt)
        try:
            async for chunk in self._provider.stream(prompt, functions):
                yield chunk
        except Exception:
            if self._fallback is not None:
                async for chunk in self._fallback.stream(prompt, functions):
                    yield chunk
                return
            raise

    __call__ = generate
