from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (TYPE_CHECKING, Any, AsyncIterator, Dict, Protocol,
                    runtime_checkable)

from pipeline.validation import ValidationResult
from plugins.resources.base import BaseResource

if TYPE_CHECKING:  # pragma: no cover
    from pipeline.state import LLMResponse


@runtime_checkable
class Resource(Protocol):
    async def initialize(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def health_check(self) -> bool: ...

    def get_metrics(self) -> dict[str, Any]: ...


class LLM(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> LLMResponse: ...

    async def __call__(self, prompt: str) -> str:
        return (await self.generate(prompt)).content

    async def stream(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError


class LLMResource(BaseResource, LLM):
    name = "llm"

    async def generate(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> LLMResponse:
        raise NotImplementedError

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        raise NotImplementedError

    __call__ = generate

    async def call_llm(self, prompt: str, sanitize: bool = False) -> str:
        if sanitize:
            from html import escape

            prompt = escape(prompt)
        return await self.generate(prompt)

    @staticmethod
    def validate_required_fields(config: Dict, fields: list[str]) -> ValidationResult:
        missing = [field for field in fields if not config.get(field)]
        if missing:
            joined = ", ".join(missing)
            return ValidationResult.error_result(f"missing required fields: {joined}")
        return ValidationResult.success_result()

    @staticmethod
    def extract_params(config: Dict, required: list[str]) -> Dict[str, Any]:
        return {k: v for k, v in config.items() if k not in required}


__all__ = ["Resource", "BaseResource", "LLM", "LLMResource"]
