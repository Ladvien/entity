from __future__ import annotations

"""LLM resource backed by an Ollama server."""

from typing import Any, Dict

from pipeline.validation import ValidationResult

from .llm.provider_resource import ProviderResource
from .llm.providers.ollama import OllamaProvider


class OllamaLLMResource(ProviderResource):
    """Resource backed by :class:`OllamaProvider`."""

    name = "ollama"
    provider_cls = OllamaProvider

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(self.provider_cls(config or {}))

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        return cls.provider_cls.validate_config(config)
