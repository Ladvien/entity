from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, List, Protocol

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.resources.database import DatabaseResource
from pipeline.stages import PipelineStage


class VectorStoreResource(Protocol):
    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None: ...

    async def query_similar(self, query: str, k: int) -> List[str]: ...


class FileSystemResource(Protocol):
    async def store(self, key: str, content: bytes) -> str: ...


class MemoryResource(ResourcePlugin):
    """Unified memory interface composing optional storage backends."""

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

    @classmethod
    def from_config(cls, config: Dict) -> "MemoryResource":
        """Instantiate backends defined in ``config``."""

        def build(section: Dict | None) -> Any:
            if not section or "type" not in section:
                return None
            module_path, class_name = section["type"].split(":", 1)
            module = import_module(module_path)
            cls_ = getattr(module, class_name)
            return cls_(section)

        database = build(config.get("database"))
        vector_store = build(config.get("vector_store"))
        filesystem = build(config.get("filesystem"))
        return cls(
            database=database,
            vector_store=vector_store,
            filesystem=filesystem,
            config=config,
        )

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def save_conversation(
        self, conversation_id: str, entries: List[ConversationEntry]
    ) -> None:
        """Persist ``entries`` using the database backend."""

        if self.database:
            await self.database.save_history(conversation_id, entries)

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        """Semantic search using the vector store backend."""

        if self.vector_store:
            return await self.vector_store.query_similar(query, k)
        return []

    async def store_file(self, key: str, content: bytes) -> str:
        """Store file ``content`` via the filesystem backend."""

        if self.filesystem:
            return await self.filesystem.store(key, content)
        raise ValueError("No filesystem backend configured")
