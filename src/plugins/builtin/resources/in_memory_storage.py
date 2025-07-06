from __future__ import annotations

"""In-memory conversation history storage."""

from typing import Dict, List

from pipeline.state import ConversationEntry
from plugins.builtin.resources.database import DatabaseResource


class InMemoryStorageResource(DatabaseResource):
    """Simple in-memory storage backend for conversation history."""

    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._data: Dict[str, List[ConversationEntry]] = {}

    async def _do_health_check(self, connection: None) -> None:
        """In-memory storage is always healthy."""
        return None

    async def health_check(self) -> bool:  # pragma: no cover - trivial
        return True

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        self._data[conversation_id] = list(history)

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        return list(self._data.get(conversation_id, []))
