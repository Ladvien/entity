from __future__ import annotations

from typing import Any, Dict, List

from pipeline.context import ConversationEntry
from pipeline.initializer import import_plugin_class
from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.resources import (DatabaseResource, FileSystemResource, Memory,
                                VectorStoreResource)
from pipeline.stages import PipelineStage


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
    """Composite memory resource composed of optional backends."""

    stages = [PipelineStage.PARSE]
    name = "memory"

    def __init__(
        self,
        database: DatabaseResource | None = None,
        vector_store: VectorStoreResource | None = None,
        filesystem: FileSystemResource | None = None,
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.database = database
        self.vector_store = vector_store
        self.filesystem = filesystem
        self._kv: Dict[str, Any] = {}

    @classmethod
    def from_config(cls, config: Dict) -> "MemoryResource":
        def build(key: str):
            cfg = config.get(key)
            if not cfg or not isinstance(cfg, dict):
                return None

            type_hint = cfg.get("type")
            if not type_hint:
                return None

            cls_obj = import_plugin_class(type_hint)
            return cls_obj(cfg)

        database = build("database")
        vector_store = build("vector_store")
        filesystem = build("filesystem")
        return cls(database, vector_store, filesystem, config)

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

    async def store_file(self, key: str, content: bytes) -> str:
        if not self.filesystem:
            raise ValueError("No filesystem backend configured")
        return await self.filesystem.store(key, content)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("database", "vector_store", "filesystem"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()
