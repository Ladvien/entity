from __future__ import annotations

from typing import Any, Dict

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class SimpleMemoryResource(ResourcePlugin):
    """Volatile key/value store shared across pipeline runs.

    This resource illustrates the *Resource Agnostic* principle by enabling
    plugins to operate without requiring an external persistence layer. All
    data is stored only in memory and is lost when the process exits.
    """

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(self, config: Dict | None = None) -> None:
        """Initialize an empty memory store."""

        super().__init__(config)
        self._store: Dict[str, Any] = {}

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        """No-op execution hook for the parse stage."""
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a stored value.

        Args:
            key: Key to look up.
            default: Value returned when ``key`` is missing.

        Returns:
            The stored value or ``default`` if not found.
        """

        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` under ``key`` in memory.

        Args:
            key: Storage key.
            value: Data to store.
        """

        self._store[key] = value

    def clear(self) -> None:
        """Remove all stored values."""

        self._store.clear()
