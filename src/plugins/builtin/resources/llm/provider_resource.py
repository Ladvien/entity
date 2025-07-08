from __future__ import annotations

"""Resource wrapper around an LLM provider."""

from typing import Any, AsyncIterator, Dict, List

from pipeline.state import LLMResponse
from pipeline.validation import ValidationResult

from ..llm_resource import LLMResource
from .providers.base import BaseProvider


class ProviderResource(LLMResource):  # type: ignore[misc]
    """Adapter that delegates calls to a provider instance."""

    name = "provider"

    def __init__(self, provider: BaseProvider) -> None:
        super().__init__()
        self._provider = provider

    @property
    def provider(self) -> BaseProvider:
        return self._provider

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        if hasattr(cls, "provider_cls"):
            return cls.provider_cls.validate_config(config)
        return ValidationResult.success_result()

    async def __aenter__(self) -> "ProviderResource":
        if hasattr(self.provider, "__aenter__"):
            await self.provider.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any | None,
    ) -> None:
        if hasattr(self.provider, "__aexit__"):
            await self.provider.__aexit__(exc_type, exc, tb)

    async def validate_runtime(self) -> ValidationResult:
        if hasattr(self.provider, "validate_runtime"):
            return await self.provider.validate_runtime()
        return ValidationResult.success_result()

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        return await self.provider.generate(prompt, functions)

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        async for chunk in self.provider.stream(prompt, functions):
            yield chunk
