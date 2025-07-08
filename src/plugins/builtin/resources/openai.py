from __future__ import annotations

"""LLM resource for OpenAI's chat completion API."""

from typing import Any, Dict

from pipeline.validation import ValidationResult

from .llm.provider_resource import ProviderResource
from .llm.providers.openai import OpenAIProvider


class OpenAIResource(ProviderResource):
    """Resource backed by :class:`OpenAIProvider`."""

    name = "openai"
    provider_cls = OpenAIProvider

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(self.provider_cls(config or {}))

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        return cls.provider_cls.validate_config(config)
