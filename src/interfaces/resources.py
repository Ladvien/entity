from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (TYPE_CHECKING, Any, AsyncIterator, Protocol,
                    runtime_checkable)

if TYPE_CHECKING:  # pragma: no cover
    from registry import ClassRegistry

from pipeline.logging import get_logger
from pipeline.state import LLMResponse
from pipeline.validation import ValidationResult


@runtime_checkable
class Resource(Protocol):
    async def initialize(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def health_check(self) -> bool: ...

    def get_metrics(self) -> dict[str, Any]: ...


class BaseResource:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    async def initialize(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def health_check(self) -> bool:
        return True

    def get_metrics(self) -> dict[str, Any]:
        return {"status": "healthy"}

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> ValidationResult:
        return ValidationResult.success_result()

    @classmethod
    def validate_dependencies(cls, registry: "ClassRegistry") -> ValidationResult:
        return ValidationResult.success_result()


class LLM(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> LLMResponse: ...

    async def __call__(self, prompt: str) -> str:
        return str((await self.generate(prompt)).content)

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

    async def stream(
        self, prompt: str, functions: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    async def __call__(self, prompt: str) -> str:
        return str((await self.generate(prompt)).content)

    async def call_llm(self, prompt: str, sanitize: bool = False) -> str:
        if sanitize:
            from html import escape

            prompt = escape(prompt)
        response = await self.generate(prompt)
        return str(response.content)

    @staticmethod
    def validate_required_fields(
        config: dict[str, Any], fields: list[str]
    ) -> ValidationResult:
        missing = [field for field in fields if not config.get(field)]
        if missing:
            joined = ", ".join(missing)
            return ValidationResult.error_result(f"missing required fields: {joined}")
        return ValidationResult.success_result()

    @staticmethod
    def extract_params(config: dict[str, Any], required: list[str]) -> dict[str, Any]:
        return {k: v for k, v in config.items() if k not in required}


__all__ = ["Resource", "BaseResource", "LLM", "LLMResource"]
