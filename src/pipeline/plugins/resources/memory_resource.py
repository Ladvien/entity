from __future__ import annotations

from typing import Any, Dict, Optional

from pipeline.initializer import import_plugin_class
from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.resources.memory import Memory
from pipeline.stages import PipelineStage


class SimpleMemoryResource(ResourcePlugin, Memory):
    """In-memory key/value store persisted across pipeline runs.

    Demonstrates **Resource Agnostic (11)** since plugins can operate with or
    without persistent storage.
    """

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._store: Dict[str, Any] = {}

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from memory."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store a value in memory."""
        self._store[key] = value

    def clear(self) -> None:
        """Remove all stored values."""
        self._store.clear()


class MemoryResource(ResourcePlugin, Memory):
    """Wrapper that delegates storage to a configurable backend."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(
        self, backend: Optional[Memory] = None, config: Dict | None = None
    ) -> None:
        super().__init__(config)
        self._backend = backend or SimpleMemoryResource({})

    @classmethod
    def from_config(cls, config: Dict) -> "MemoryResource":
        backend_cfg = config.get("backend", {})
        backend_type = backend_cfg.get(
            "type",
            "pipeline.plugins.resources.memory_resource:SimpleMemoryResource",
        )
        backend_cls = import_plugin_class(backend_type)
        backend = backend_cls(backend_cfg)
        return cls(backend, config)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._backend.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._backend.set(key, value)

    def clear(self) -> None:
        self._backend.clear()

    @classmethod
    def validate_config(cls, config: Dict) -> "ValidationResult":
        backend = config.get("backend")
        if backend is not None and not isinstance(backend, dict):
            return ValidationResult(
                success=False, error_message="'backend' must be a mapping"
            )
        return ValidationResult.success_result()
