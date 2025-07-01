from __future__ import annotations

from typing import Dict, Type

from pipeline.plugins import ValidationResult
from pipeline.resources.llm import LLMResource

from .providers import (
    ClaudeProvider,
    EchoProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)


class UnifiedLLMResource(LLMResource):
    """LLM resource selecting a provider at runtime."""

    name = "llm"
    aliases = ["llm"]

    PROVIDERS: Dict[str, Type[LLMResource]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "echo": EchoProvider,
    }

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        provider_name = str(self.config.get("provider", "echo")).lower()
        provider_cls = self.PROVIDERS.get(provider_name, EchoProvider)
        self._provider = provider_cls(self.config)
        self.aliases = ["llm", provider_name]
        fallback_name = str(self.config.get("fallback", "echo")).lower()
        if fallback_name == provider_name:
            self._fallback = None
        else:
            fallback_cls = self.PROVIDERS.get(fallback_name, EchoProvider)
            self._fallback = fallback_cls(self.config)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        provider_name = str(config.get("provider", "echo")).lower()
        provider_cls = cls.PROVIDERS.get(provider_name)
        if not provider_cls:
            return ValidationResult.error_result(
                f"Unknown LLM provider '{provider_name}'"
            )
        return provider_cls.validate_config(config)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def generate(self, prompt: str) -> str:
        try:
            return await self._provider.generate(prompt)
        except Exception:
            if self._fallback is not None:
                return await self._fallback.generate(prompt)
            raise

    __call__ = generate
