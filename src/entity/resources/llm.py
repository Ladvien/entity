"""Canonical LLM resource."""

from __future__ import annotations

from typing import Any, Dict

from ..core.plugins import ValidationResult
from entity.config.models import LLMConfig
from pydantic import ValidationError

from ..core.resources.container import PoolConfig, ResourcePool
from .base import AgentResource
from .interfaces.llm import LLMResource


class LLM(AgentResource):
    """Simple LLM wrapper."""

    name = "llm"
    dependencies = ["llm_provider"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.provider: LLMResource | None = None
        self._pool: ResourcePool[LLMResource] | None = None

    async def initialize(self) -> None:
        if self.provider is None:
            return
        pool_cfg = PoolConfig(**self.config.get("pool", {}))
        self._pool = ResourcePool(self._create_provider, pool_cfg)
        await self._pool.initialize()

    async def _create_provider(self) -> LLMResource:
        assert self.provider is not None
        return self.provider

    def get_client_pool(self) -> ResourcePool[LLMResource] | None:
        return self._pool

    def get_pool_metrics(self) -> Dict[str, int]:
        if self._pool is None:
            return {"total_size": 0, "in_use": 0, "available": 0}
        return self._pool.metrics()

    async def generate(self, prompt: str) -> Any:
        if self.provider is None:
            return ""
        if self._pool is None:
            return await self.provider.generate(prompt)
        async with self._pool as provider:
            return await provider.generate(prompt)

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            LLMConfig.parse_obj(config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def validate_runtime(self) -> ValidationResult:
        """Validate underlying provider connectivity."""
        if self.provider and hasattr(self.provider, "validate_runtime"):
            result = await self.provider.validate_runtime()
            if not result.success:
                return ValidationResult.error_result(f"provider: {result.message}")
        return ValidationResult.success_result()
