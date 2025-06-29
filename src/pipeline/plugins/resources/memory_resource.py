from __future__ import annotations

from typing import Any, Dict

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class SimpleMemoryResource(ResourcePlugin):
    """In-memory key/value store persisted across pipeline runs."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(self) -> None:
        super().__init__()
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
