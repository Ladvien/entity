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
<<<<<<< HEAD
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
=======
        provider_names: List[str] = []
        if "providers" in self.config:
            provider_names = [str(p).lower() for p in self.config.get("providers", [])]
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2
        else:
            primary = str(self.config.get("provider", "echo")).lower()
            provider_names.append(primary)
            fallback = self.config.get("fallback")
            if fallback:
                provider_names.append(str(fallback).lower())

        clean_config = {
            k: v
            for k, v in self.config.items()
            if k not in {"provider", "fallback", "providers", "model_map"}
        }

        self._providers: List[LLMResource] = []
        for name in provider_names:
            cls = self.PROVIDERS.get(name, EchoProvider)
            result = cls.validate_config(clean_config)
            if not result.success:
                raise ValueError(result.error_message)
            self._providers.append(cls(clean_config))
        if not self._providers:
            self._providers.append(EchoProvider(clean_config))

        self._model_map: Dict[str, str] = self.config.get("model_map", {})

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        providers = config.get("providers")
        if providers:
            for name in providers:
                if name not in cls.PROVIDERS:
                    return ValidationResult.error_result(
                        f"Unknown LLM provider '{name}'"
                    )
            first = providers[0]
        else:
            first = str(config.get("provider", "echo")).lower()
            if first not in cls.PROVIDERS:
                return ValidationResult.error_result(f"Unknown LLM provider '{first}'")
        return cls.PROVIDERS[first].validate_config(config)

    def _select_model(self, prompt: str) -> None:
        for key, model in self._model_map.items():
            if key.lower() in prompt.lower():
<<<<<<< HEAD
                if hasattr(self._provider, "http"):
                    self._provider.http.model = model
=======
                for provider in self._providers:
                    if hasattr(provider, "http"):
                        provider.http.model = model
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2
                break

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        self._select_model(prompt)
<<<<<<< HEAD
        try:
            return await self._provider.generate(prompt, functions)
        except Exception:
            if self._fallback is not None:
                return await self._fallback.generate(prompt, functions)
            raise
=======
        last_exc: Exception | None = None
        for provider in self._providers:
            try:
                return await provider.generate(prompt, functions)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                continue
        if last_exc:
            raise last_exc
        raise RuntimeError("No provider available")
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        self._select_model(prompt)
<<<<<<< HEAD
        try:
            async for chunk in self._provider.stream(prompt, functions):
                yield chunk
        except Exception:
            if self._fallback is not None:
                async for chunk in self._fallback.stream(prompt, functions):
                    yield chunk
                return
            raise
=======
        last_exc: Exception | None = None
        for provider in self._providers:
            try:
                async for chunk in provider.stream(prompt, functions):
                    yield chunk
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                continue
        if last_exc:
            raise last_exc
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2

    __call__ = generate
