from __future__ import annotations

from typing import Any, Dict

from pipeline.base_plugins import ResourcePlugin
from pipeline.cache import CacheBackend, InMemoryCache
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<< yvh9jp-codex/configure-pre-commit-and-enforce-quality-checks
from pipeline.context import PluginContext
from pipeline.initializer import import_plugin_class
======
from pipeline.interfaces import import_plugin_class
>>>>>> main
=======
from pipeline.context import PluginContext
from pipeline.interfaces import import_plugin_class
>>>>>>> ade5ea02fe57934389c67708aacbf514ac2c4c3b
=======
from pipeline.context import PluginContext
from pipeline.interfaces import import_plugin_class
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2
=======
from pipeline.context import PluginContext
from pipeline.interfaces import import_plugin_class
>>>>>>> 05754355a96c3f8124313438180394671344b866
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
        await self._backend.delete(key)
