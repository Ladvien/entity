from __future__ import annotations

"""Runtime LLM resource selecting a provider."""


from typing import Any, AsyncIterator, Dict, List, Type

from interfaces import import_plugin_class
from interfaces.resources import LLMResource
from pipeline.state import LLMResponse
from pipeline.user_plugins import ValidationResult


class UnifiedLLMResource(LLMResource):
    """LLM resource selecting a provider at runtime."""

    name = "llm"

    PROVIDERS: Dict[str, str] = {
        "openai": "plugins.llm.providers.openai:OpenAIProvider",
        "ollama": "plugins.llm.providers.ollama:OllamaProvider",
        "gemini": "plugins.llm.providers.gemini:GeminiProvider",
        "claude": "plugins.llm.providers.claude:ClaudeProvider",
        "bedrock": "plugins.llm.providers.bedrock:BedrockProvider",
        "echo": "plugins.llm.providers.echo:EchoProvider",
    }

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        provider_names: List[str] = []
        if "providers" in self.config:
            provider_names = [str(p).lower() for p in self.config.get("providers", [])]
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
            path = self.PROVIDERS.get(name, self.PROVIDERS["echo"])
            cls = import_plugin_class(path)
            result = cls.validate_config(clean_config)
            if not result.success:
                raise ValueError(result.error_message)
            self._providers.append(cls(clean_config))
        if not self._providers:
            default_cls = import_plugin_class(self.PROVIDERS["echo"])
            self._providers.append(default_cls(clean_config))

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
        path = cls.PROVIDERS[first]
        provider_cls = import_plugin_class(path)
        return provider_cls.validate_config(config)

    def _select_model(self, prompt: str) -> None:
        for key, model in self._model_map.items():
            if key.lower() in prompt.lower():
                for provider in self._providers:
                    if hasattr(provider, "http"):
                        provider.http.model = model
                break

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        self._select_model(prompt)
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

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        self._select_model(prompt)
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

    __call__ = generate
