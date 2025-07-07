from __future__ import annotations

from typing import Any, Dict

from common_interfaces import import_plugin_class
from pipeline.base_plugins import ResourcePlugin
from pipeline.cache import CacheBackend, InMemoryCache
from pipeline.context import PluginContext
from pipeline.stages import PipelineStage
from pipeline.validation import ValidationResult


class CacheResource(ResourcePlugin, CacheBackend):
    """Resource wrapper providing a cache backend."""

    stages = [PipelineStage.PARSE]
    name = "cache"

    def __init__(
        self, backend: CacheBackend | None = None, config: Dict | None = None
    ) -> None:
        super().__init__(config or {})
        self._backend = backend or InMemoryCache()

    @classmethod
    def from_config(cls, config: Dict) -> "CacheResource":
        backend_cfg = config.get("backend") or {}
        backend = cls._build_backend(backend_cfg)
        return cls(backend, config)

    @staticmethod
    def _build_backend(cfg: Dict) -> CacheBackend:
        type_hint = cfg.get("type")
        if not type_hint:
            return InMemoryCache()
        cls_obj = import_plugin_class(type_hint)
        kwargs = {k: v for k, v in cfg.items() if k != "type"}
        return cls_obj(**kwargs)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        backend = config.get("backend")
        if backend is not None and not isinstance(backend, dict):
            return ValidationResult.error_result("'backend' must be a mapping")
        return ValidationResult.success_result()

    async def _execute_impl(
        self, context: PluginContext
    ) -> None:  # pragma: no cover - not used
        """Cache resource does not execute in the pipeline."""
        return None

    async def get(self, key: str) -> Any:
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self._backend.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        delete_fn = getattr(self._backend, "delete", None)
        if callable(delete_fn):
            await delete_fn(key)

    async def clear(self) -> None:
        await self._backend.clear()
