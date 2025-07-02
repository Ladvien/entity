from __future__ import annotations

<<<<<<< HEAD
from typing import Any, Dict, List

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.plugins.resources.vector_memory import VectorMemoryResource
from pipeline.resources.database import DatabaseResource
=======
from typing import Any, Dict, Optional

from pipeline.initializer import import_plugin_class
from pipeline.plugins import ResourcePlugin, ValidationResult
>>>>>>> 675e5906c4d22f829a34870d1fbc1d9cbdba58ad
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

<<<<<<< HEAD
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
=======

class MemoryResource(ResourcePlugin, Memory):
    """Wrapper that delegates storage to a configurable backend."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(
        self, backend: Optional[Memory] = None, config: Dict | None = None
    ) -> None:
        super().__init__(config)
        self._backend = backend or SimpleMemoryResource({})

    @classmethod
    def from_config(cls, config: Dict) -> "MemoryResource":
        backend_cfg = config.get("backend", {})
        backend_type = backend_cfg.get(
            "type",
            "pipeline.plugins.resources.memory_resource:SimpleMemoryResource",
        )
        backend_cls = import_plugin_class(backend_type)
        backend = backend_cls(backend_cfg)
        return cls(backend, config)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._backend.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._backend.set(key, value)

    def clear(self) -> None:
        self._backend.clear()

    @classmethod
    def validate_config(cls, config: Dict) -> "ValidationResult":
        backend = config.get("backend")
        if backend is not None and not isinstance(backend, dict):
            return ValidationResult(
                success=False, error_message="'backend' must be a mapping"
            )
        return ValidationResult.success_result()
>>>>>>> 675e5906c4d22f829a34870d1fbc1d9cbdba58ad
