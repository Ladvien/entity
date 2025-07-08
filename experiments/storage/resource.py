from __future__ import annotations

"""Experimental StorageResource supporting composable backends.
Not for production use."""

from contextlib import asynccontextmanager
from typing import Dict, List

from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.context import ConversationEntry
from pipeline.exceptions import ResourceError
from pipeline.stages import PipelineStage
from plugins.builtin.resources.database import DatabaseResource
from plugins.builtin.resources.filesystem import FileSystemResource
from plugins.builtin.resources.vector_store import VectorStoreResource


class StorageResource(ResourcePlugin):
    """Compose database, vector store, and filesystem backends."""

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

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        """Resource plugins are not executed directly."""
        return None

    async def initialize(self) -> None:  # pragma: no cover - simple passthrough
        for backend in (self.database, self.vector_store, self.filesystem):
            if hasattr(backend, "initialize") and callable(backend.initialize):
                await backend.initialize()

    async def shutdown(self) -> None:  # pragma: no cover - simple passthrough
        for backend in (self.database, self.vector_store, self.filesystem):
            if hasattr(backend, "shutdown") and callable(backend.shutdown):
                await backend.shutdown()

    @asynccontextmanager
    async def connection(self):
        """Yield a pooled database connection if available."""

        if self.database is None:
            raise ResourceError("No database backend configured")
        async with self.database.connection() as conn:
            yield conn

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
            raise ResourceError("No filesystem backend configured")
        return await self.filesystem.store(key, content)

    async def load_file(self, key: str) -> bytes:
        if not self.filesystem:
            raise ResourceError("No filesystem backend configured")
        return await self.filesystem.load(key)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("database", "vector_store", "filesystem"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()


__all__ = ["StorageResource"]
