from __future__ import annotations

"""Simplified in-memory storage resource."""

from typing import Any, Dict, List

from ..core.plugins import ResourcePlugin, ValidationResult


class Memory(ResourcePlugin):
    """Store key/value data and conversation history."""

    name = "memory"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._kv: Dict[str, Any] = {}
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}

    async def _execute_impl(self, context: Any) -> None:  # noqa: D401, ARG002
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------

    def memory(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a persisted value."""
        return self._kv.get(key, default)

    def remember(self, key: str, value: Any) -> None:
        """Persist ``value`` for later retrieval."""
        self._kv[key] = value

    # Backwards compatibility
    get = memory
    set = remember

    def clear(self) -> None:
        self._kv.clear()

    async def save_conversation(
        self, conversation_id: str, history: List[Dict[str, Any]]
    ) -> None:
        self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        return list(self._conversations.get(conversation_id, []))

    async def search_similar(self, query: str, k: int = 5) -> List[str]:  # noqa: ARG002
        return []

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
