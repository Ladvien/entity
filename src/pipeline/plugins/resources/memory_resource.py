from __future__ import annotations

from typing import Any, Dict

<<<<<<< HEAD
from pipeline.base_plugins import ResourcePlugin
=======
from pipeline.plugins import ResourcePlugin
from pipeline.resources.memory import Memory
>>>>>>> 66045f0cc3ea9a831e3ec579ceb40548cd673716
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
        self._memory: Dict[str, Any] = {}

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from memory."""
        return self._memory.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store a value in memory."""
        self._memory[key] = value

    def clear(self) -> None:
        """Remove all stored values."""
        self._memory.clear()
