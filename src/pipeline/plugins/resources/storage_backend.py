<<<<<<< HEAD
from pipeline.resources.storage import StorageBackend, StorageResource

__all__ = ["StorageBackend", "StorageResource"]
=======
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class StorageBackend(ResourcePlugin):
    """Common interface for conversation storage backends."""

    name = "database"
    stages = [PipelineStage.PARSE]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._history_table = self.config.get("history_table")
        self._schema = self.config.get("db_schema")

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    async def acquire(self) -> Any:
        raise NotImplementedError

    async def release(self, connection: Any) -> None:
        raise NotImplementedError

    async def execute(self, query: str, *args: Any) -> Any:
        raise NotImplementedError

    async def fetch(self, query: str, *args: Any) -> Any:
        raise NotImplementedError

    async def fetchrow(self, query: str, *args: Any) -> Any:
        raise NotImplementedError

    async def fetchval(self, query: str, *args: Any) -> Any:
        raise NotImplementedError

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._history_table is None:
            return
        for entry in history:
            await self.execute(
                f"INSERT INTO {self._table_name()} "
                "(conversation_id, role, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                conversation_id,
                entry.role,
                entry.content,
                json.dumps(entry.metadata),
                entry.timestamp,
            )

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        if self._history_table is None:
            return []
        rows = await self.fetch(
            f"SELECT role, content, metadata, timestamp FROM {self._table_name()} "
            "WHERE conversation_id=? ORDER BY timestamp",
            conversation_id,
        )
        history: List[ConversationEntry] = []
        for row in rows:
            metadata = row[2] if isinstance(row, (list, tuple)) else row.get("metadata")
            if not isinstance(metadata, dict):
                metadata = json.loads(metadata) if metadata else {}
            history.append(
                ConversationEntry(
                    content=(
                        row[1] if isinstance(row, (list, tuple)) else row.get("content")
                    ),
                    role=row[0] if isinstance(row, (list, tuple)) else row.get("role"),
                    timestamp=(
                        row[3]
                        if isinstance(row, (list, tuple))
                        else row.get("timestamp")
                    ),
                    metadata=metadata,
                )
            )
        return history

    async def health_check(self) -> bool:
        try:
            await self.fetch("SELECT 1")
            return True
        except Exception:  # noqa: BLE001
            return False

    def _table_name(self) -> str:
        return (
            f"{self._schema + '.' if self._schema else ''}{self._history_table}"
            if self._history_table
            else ""
        )
>>>>>>> 41e9ce33055fea658287c473f9fa43fe2b5cbcc7
