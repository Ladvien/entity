from __future__ import annotations

"""DuckDB-based conversation history storage."""
import asyncio
import json
import re
from typing import TYPE_CHECKING, Dict, List, Optional

import duckdb

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from pipeline.state import ConversationEntry

from plugins.builtin.resources.database import DatabaseResource


class DuckDBDatabaseResource(DatabaseResource):
    """DuckDB-based conversation history storage."""

    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._path = self.config.get("path", ":memory:")
        table = self.config.get("history_table")
        self._history_table = self._sanitize_identifier(table) if table else None
        self._connection: Optional[duckdb.DuckDBPyConnection] = None

    @staticmethod
    def _sanitize_identifier(name: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid identifier: {name}")
        return name

    async def initialize(self) -> None:
        self._connection = await asyncio.to_thread(duckdb.connect, self._path)
        if self._history_table:
            await asyncio.to_thread(
                self._connection.execute,
                f"""CREATE TABLE IF NOT EXISTS {self._history_table} (
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                metadata TEXT,
                timestamp TIMESTAMP
            )""",
            )

    async def health_check(self) -> bool:
        if self._connection is None:
            return False
        try:
            await self._do_health_check(self._connection)
            return True
        except Exception:
            return False

    async def _do_health_check(self, connection: duckdb.DuckDBPyConnection) -> None:
        await asyncio.to_thread(connection.execute, "SELECT 1")

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._connection is None or not self._history_table:
            return
        for entry in history:
            await asyncio.to_thread(
                self._connection.execute,
                (
                    f"INSERT INTO {self._history_table} "
                    "(conversation_id, role, content, metadata, timestamp) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                [
                    conversation_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp,
                ],
            )

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        if self._connection is None or not self._history_table:
            return []
        rel = await asyncio.to_thread(
            self._connection.execute,
            (
                f"SELECT role, content, metadata, timestamp FROM {self._history_table} "
                "WHERE conversation_id = ? ORDER BY timestamp"
            ),
            [conversation_id],
        )
        rows = await asyncio.to_thread(rel.fetchall)
        history: List[ConversationEntry] = []
        for role, content, metadata, ts in rows:
            metadata_dict = json.loads(metadata) if metadata else {}
            history.append(
                ConversationEntry(
                    content=content,
                    role=role,
                    metadata=metadata_dict,
                    timestamp=ts,
                )
            )
        return history

    async def shutdown(self) -> None:
        if self._connection is not None:
            await asyncio.to_thread(self._connection.close)
            self._connection = None
