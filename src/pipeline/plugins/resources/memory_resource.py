from __future__ import annotations

from typing import Any, Dict, List

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.plugins.resources.vector_memory import VectorMemoryResource
from pipeline.resources.database import DatabaseResource
from pipeline.resources.memory import Memory
from pipeline.stages import PipelineStage


class MemoryResource(ResourcePlugin, Memory):
    """Unified memory interface combining optional backends."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(
        self,
        database: DatabaseResource | None = None,
        vector_store: VectorMemoryResource | None = None,
        config: Dict | None = None,
    ) -> None:
        super().__init__(config)
        self.database = database
        self.vector_store = vector_store
        self._store: Dict[str, Any] = {}

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()

    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self.database:
            await self.database.save_history(conversation_id, history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        if self.database:
            return await self.database.load_history(conversation_id)
        return []

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        if self.vector_store:
            return await self.vector_store.query_similar(query, k)
        return []


class SimpleMemoryResource(MemoryResource):
    """In-memory key/value store persisted across pipeline runs."""

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(None, None, config)
        self._conversations: Dict[str, List[ConversationEntry]] = {}

    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        return list(self._conversations.get(conversation_id, []))
