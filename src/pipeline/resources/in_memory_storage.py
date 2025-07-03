from __future__ import annotations

from typing import Dict, List

from pipeline.context import ConversationEntry
from pipeline.resources.base import BaseResource
from pipeline.resources.storage import StorageBackend


class InMemoryStorageResource(BaseResource, StorageBackend):
    """Simple in-memory storage backend for conversation history."""

    name = "storage"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._data: Dict[str, List[ConversationEntry]] = {}

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        self._data[conversation_id] = list(history)

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        return list(self._data.get(conversation_id, []))
