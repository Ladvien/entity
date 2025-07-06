from __future__ import annotations

"""Memory resource supporting in-memory, SQL/NoSQL, and vector store backends."""


from typing import Any, Dict, List

<<<<<<< HEAD
from plugins.builtin.resources.memory_filesystem import MemoryFileSystem
from plugins.builtin.resources.memory_storage import MemoryStorage
from plugins.builtin.resources.memory_vector_store import MemoryVectorStore

=======
>>>>>>> c72003e014c664863289e303211be6661160fdc6
from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.context import ConversationEntry
from pipeline.stages import PipelineStage

from .memory import Memory


class SimpleMemoryResource(ResourcePlugin, Memory):
    """Basic in-memory key/value store."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._store: Dict[str, Any] = {}

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()


class MemoryResource(ResourcePlugin, Memory):
    """Combine in-memory storage with optional database and vector backends."""

    stages = [PipelineStage.PARSE]
    name = "memory"
    dependencies = ["storage", "vector", "filesystem"]

    def __init__(
        self,
<<<<<<< HEAD
        storage: MemoryStorage | None = None,
        vector: MemoryVectorStore | None = None,
        filesystem: MemoryFileSystem | None = None,
=======
        database: DatabaseResource | None = None,
        vector_store: Any | None = None,
>>>>>>> c72003e014c664863289e303211be6661160fdc6
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.storage = storage
        self.vector = vector
        self.filesystem = filesystem
        self._kv: Dict[str, Any] = {}

    @classmethod
    def from_config(cls, config: Dict) -> "MemoryResource":
        return cls(config=config)

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
        if self.storage:
            await self.storage.save_history(conversation_id, history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        if self.storage:
            return await self.storage.load_history(conversation_id)
        return []

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        if self.vector:
            return await self.vector.query_similar(query, k)
        return []

    async def store_file(self, key: str, content: bytes) -> str:
        if not self.filesystem:
            raise ValueError("No filesystem backend configured")
        return await self.filesystem.store(key, content)

    async def load_file(self, key: str) -> bytes:
        if not self.filesystem:
            raise ValueError("No filesystem backend configured")
        return await self.filesystem.load(key)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("storage", "vector", "filesystem"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()
