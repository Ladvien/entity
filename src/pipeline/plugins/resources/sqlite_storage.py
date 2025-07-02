from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

import aiosqlite

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.resources.storage import StorageBackend
from pipeline.stages import PipelineStage


class SQLiteStorageResource(ResourcePlugin, StorageBackend):
    """SQLite-based conversation history storage."""

    stages = [PipelineStage.PARSE]
    name = "storage"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._path = self.config.get("path", ":memory:")
        self._table = self.config.get("history_table", "chat_history")
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {self._table} (
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                metadata TEXT,
                timestamp REAL
            )"""
        )
        await self._conn.commit()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._conn is None:
            return
        for entry in history:
            await self._conn.execute(
                f"INSERT INTO {self._table} (conversation_id, role, content, metadata, timestamp)"  # nosec B608
                " VALUES (?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp.timestamp(),
                ),
            )
        await self._conn.commit()

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        if self._conn is None:
            return []
        cursor = await self._conn.execute(
            f"SELECT role, content, metadata, timestamp FROM {self._table} "  # nosec B608
            "WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        history: List[ConversationEntry] = []
        for role, content, metadata, ts in rows:
            metadata_dict = json.loads(metadata) if metadata else {}
            history.append(
                ConversationEntry(
                    content=content,
                    role=role,
                    metadata=metadata_dict,
                    timestamp=datetime.fromtimestamp(ts),
                )
            )
        return history

    async def shutdown(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None


SQLiteStorage = SQLiteStorageResource
__all__ = ["SQLiteStorageResource", "SQLiteStorage"]
