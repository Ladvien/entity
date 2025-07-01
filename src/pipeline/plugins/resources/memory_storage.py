from __future__ import annotations

import json
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, DefaultDict, Dict, List

from pipeline.context import ConversationEntry

from .storage_backend import StorageBackend


class MemoryStorage(StorageBackend):
    """In-memory storage backend for testing and ephemeral runs."""

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._data: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)

    async def initialize(self) -> None:  # pragma: no cover - no setup needed
        return None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator["MemoryStorage"]:
        yield self

    async def acquire(self) -> "MemoryStorage":  # pragma: no cover - not used
        return self

    async def release(self, connection: Any) -> None:  # pragma: no cover - no-op
        return None

    async def execute(self, query: str, *args: Any) -> Any:
        if self._history_table and query.lower().startswith("insert into"):
            self._data[self._table_name()].append(
                {
                    "conversation_id": args[0],
                    "role": args[1],
                    "content": args[2],
                    "metadata": (
                        json.loads(args[3]) if isinstance(args[3], str) else args[3]
                    ),
                    "timestamp": args[4],
                }
            )

    async def fetch(self, query: str, *args: Any) -> Any:
        if self._history_table and query.lower().startswith("select"):
            convo_id = args[0]
            rows = [
                {
                    "role": r["role"],
                    "content": r["content"],
                    "metadata": r["metadata"],
                    "timestamp": r["timestamp"],
                }
                for r in self._data[self._table_name()]
                if r["conversation_id"] == convo_id
            ]
            return rows
        return []

    async def fetchrow(self, query: str, *args: Any) -> Any:
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None

    async def fetchval(self, query: str, *args: Any) -> Any:
        row = await self.fetchrow(query, *args)
        if row is None:
            return None
        if isinstance(row, dict):
            return next(iter(row.values()))
        return row[0]

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        for entry in history:
            await self.execute(
                f"INSERT INTO {self._table_name()} (conversation_id, role, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                conversation_id,
                entry.role,
                entry.content,
                json.dumps(entry.metadata),
                entry.timestamp,
            )

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        rows = await self.fetch(
            f"SELECT role, content, metadata, timestamp FROM {self._table_name()} WHERE conversation_id=? ORDER BY timestamp",
            conversation_id,
        )
        history: List[ConversationEntry] = []
        for row in rows:
            metadata = row["metadata"]
            history.append(
                ConversationEntry(
                    content=row["content"],
                    role=row["role"],
                    timestamp=row["timestamp"],
                    metadata=metadata,
                )
            )
        return history

    async def health_check(self) -> bool:
        return True
