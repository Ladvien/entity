from __future__ import annotations

"""Memory resource supporting in-memory, SQL/NoSQL, and vector store backends."""

from typing import Any, Dict, List

from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.context import ConversationEntry
from pipeline.stages import PipelineStage
from plugins.builtin.resources.vector_store import VectorStoreResource

from .database import DatabaseResource
from .memory import Memory


class SimpleMemoryResource(ResourcePlugin, Memory):
    """Basic in-memory key/value store with conversation support."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._store: Dict[str, Any] = {}
        self._conversations: Dict[str, List[ConversationEntry]] = {}

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
        self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        return list(self._conversations.get(conversation_id, []))


class MemoryResource(ResourcePlugin, Memory):
    """Combine in-memory storage with optional database and vector backends."""

    stages = [PipelineStage.PARSE]
    name = "memory"
    dependencies = ["database", "vector_store"]

    def __init__(
        self,
        database: DatabaseResource | None = None,
        vector_store: VectorStoreResource | None = None,
        config: Dict | None = None,
        *,
        storage: DatabaseResource | None = None,
    ) -> None:
        """Initialize the resource.

        Parameters
        ----------
        database:
            Backend used to persist conversation history.
        vector_store:
            Backend used for similarity search.
        config:
            Optional configuration mapping.
        storage:
            Keyword-only alias for ``database`` kept for backward
            compatibility.
        """

        super().__init__(config or {})
        if storage is not None and database is None:
            database = storage
        elif storage is not None and storage is not database:
            raise ValueError("'database' and 'storage' refer to different objects")
        self.database = database
        self.vector_store = vector_store
        self._kv: Dict[str, Any] = {}

    @classmethod
    def from_config(cls, config: Dict) -> "MemoryResource":
        return cls(None, None, config=config)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._kv.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._kv[key] = value

    def clear(self) -> None:
        self._kv.clear()

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

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("database", "storage", "vector_store"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()
