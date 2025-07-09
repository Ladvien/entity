from __future__ import annotations

"""In-memory database resource for conversation history."""

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from pipeline.state import ConversationEntry
else:
    from pipeline.state import ConversationEntry

from plugins.builtin.resources.database import DatabaseResource


class MemoryStorage(DatabaseResource):
    """Store conversation history purely in memory."""

    name = "database"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._data: Dict[str, List[ConversationEntry]] = {}

    async def _do_health_check(self, connection: None) -> None:  # pragma: no cover
        return None

    async def health_check(self) -> bool:  # pragma: no cover - trivial
        return True

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        self._data[conversation_id] = list(history)

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        return list(self._data.get(conversation_id, []))
