from __future__ import annotations

"""Composite storage resource for history, vectors and file data."""

from typing import Dict, List

from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.context import ConversationEntry
from pipeline.stages import PipelineStage

from .database import DatabaseResource
from .filesystem import FileSystemResource
from .vector_store import VectorStoreResource


class StorageResource(ResourcePlugin):
    """Combine database, vector store and filesystem into one resource."""

    stages = [PipelineStage.PARSE]
    name = "storage"
    dependencies = ["database", "vector_store", "filesystem"]

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

    @classmethod
    def from_config(cls, config: Dict) -> "StorageResource":
        return cls(config=config)

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self.database:
            await self.database.save_history(conversation_id, history)

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
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

    async def load_file(self, key: str) -> bytes:
        if not self.filesystem:
            raise ValueError("No filesystem backend configured")
        return await self.filesystem.load(key)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("database", "vector_store", "filesystem"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()


__all__ = ["StorageResource"]
