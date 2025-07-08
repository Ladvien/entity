from __future__ import annotations

"""SQLite-based conversation history storage."""
import json
import re
from datetime import datetime
from importlib import util as import_util
from typing import TYPE_CHECKING, Dict, List, Optional

import aiosqlite

from pipeline.observability.tracing import start_span
from pipeline.stages import PipelineStage
from pipeline.validation import ValidationResult

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from pipeline.state import ConversationEntry
else:
    from pipeline.state import ConversationEntry

from plugins.builtin.resources.database import DatabaseResource


class SQLiteStorageResource(DatabaseResource):
    """SQLite-based conversation history storage."""

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._path = self.config.get("path", ":memory:")
        table = self.config.get("history_table", "chat_history")
        self._table = self._sanitize_identifier(table)
        self._conn: Optional[aiosqlite.Connection] = None

    @staticmethod
    def _sanitize_identifier(name: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid identifier: {name}")
        return name

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

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._conn is None:
            return
        async with start_span("SQLiteStorageResource.save_history"):
            for entry in history:
                await self._conn.execute(
                    (
                        f"INSERT INTO {self._table} "  # nosec
                        "(conversation_id, role, content, metadata, timestamp)"
                        " VALUES (?, ?, ?, ?, ?)"
                    ),
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
        async with start_span("SQLiteStorageResource.load_history"):
            cursor = await self._conn.execute(
                f"SELECT role, content, metadata, timestamp FROM {self._table} "  # nosec
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

    async def health_check(self) -> bool:
        if self._conn is None:
            return False
        try:
            await self._conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def _do_health_check(self, connection: aiosqlite.Connection) -> None:
        await connection.execute("SELECT 1")
