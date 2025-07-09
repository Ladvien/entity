from __future__ import annotations

"""Unified memory resource with optional persistence and search."""

from typing import Any, Dict, List, TYPE_CHECKING

from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.context import ConversationEntry
from pipeline.stages import PipelineStage
from plugins.builtin.resources.vector_store import VectorStoreResource
from registry import SystemRegistries

from ..conversation_manager import ConversationManager
from ..manager import PipelineManager
from .database import DatabaseResource

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    pass


class Memory(ResourcePlugin):
    """Store key/value data and conversation history."""

    stages = [PipelineStage.PARSE]
    name = "memory"
    dependencies = ["database", "vector_store"]

    def __init__(
        self,
        database: DatabaseResource | None = None,
        vector_store: VectorStoreResource | None = None,
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.database = database
        self.vector_store = vector_store
        self._kv: Dict[str, Any] = {}
        self._conversations: Dict[str, List[ConversationEntry]] = {}
        self._conversation_manager: ConversationManager | None = None

    @classmethod
    def from_config(cls, config: Dict) -> "Memory":
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
        else:
            self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        if self.database:
            return await self.database.load_history(conversation_id)
        return list(self._conversations.get(conversation_id, []))

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        if self.vector_store:
            return await self.vector_store.query_similar(query, k)
        return []

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("database", "vector_store"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()

    def get_conversation_manager(
        self,
        registries: SystemRegistries,
        pipeline_manager: PipelineManager | None = None,
        *,
        history_limit: int | None = None,
    ) -> ConversationManager:
        if self._conversation_manager is None:
            self._conversation_manager = ConversationManager(
                registries,
                pipeline_manager,
                history_limit=history_limit,
            )
        return self._conversation_manager
