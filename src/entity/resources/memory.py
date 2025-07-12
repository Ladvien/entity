"""Unified Memory resource without in-memory state."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
import json

from .base import AgentResource
from .interfaces.database import DatabaseResource as DatabaseInterface
from .interfaces.vector_store import VectorStoreResource as VectorStoreInterface
from ..core.plugins import ValidationResult
from ..core.state import ConversationEntry


class Memory(AgentResource):
    """Persist conversations, key/value pairs and vectors."""

    name = "memory"
    dependencies: list[str] = ["database", "vector_store"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.database: DatabaseInterface | None = None
        self.vector_store: VectorStoreInterface | None = None
        self._pool: Any | None = None
        self._kv_table = self.config.get("kv_table", "memory_kv")
        self._history_table = self.config.get("history_table", "conversation_history")

    async def initialize(self) -> None:
        if self.database is not None:
            self._pool = self.database.get_connection_pool()
            async with self.database.connection() as conn:
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {self._kv_table} (key TEXT PRIMARY KEY, value TEXT)"
                )
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {self._history_table} ("
                    "conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)"
                )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any | None = None) -> Any:
        if self._pool is None:
            return default
        row = self._pool.execute(
            f"SELECT value FROM {self._kv_table} WHERE key = ?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value: Any) -> None:
        if self._pool is None:
            return
        self._pool.execute(
            f"INSERT OR REPLACE INTO {self._kv_table} VALUES (?, ?)",
            (key, json.dumps(value)),
        )

    remember = set

    def clear(self) -> None:
        if self._pool is not None:
            self._pool.execute(f"DELETE FROM {self._kv_table}")

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self._pool is None:
            return
        self._pool.execute(
            f"DELETE FROM {self._history_table} WHERE conversation_id = ?",
            (conversation_id,),
        )
        for entry in history:
            self._pool.execute(
                f"INSERT INTO {self._history_table} VALUES (?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp.isoformat(),
                ),
            )

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        if self._pool is None:
            return []
        rows = self._pool.execute(
            f"SELECT role, content, metadata, timestamp FROM {self._history_table} "
            "WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()
        result: List[ConversationEntry] = []
        for row in rows:
            metadata = json.loads(row[2]) if row[2] else {}
            result.append(
                ConversationEntry(
                    content=row[1],
                    role=row[0],
                    timestamp=datetime.fromisoformat(row[3]),
                    metadata=metadata,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Vector helpers
    # ------------------------------------------------------------------
    async def add_embedding(self, text: str) -> None:
        if self.vector_store is not None:
            await self.vector_store.add_embedding(text)

    async def search_similar(self, text: str, k: int = 5) -> List[str]:
        if self.vector_store is None:
            return []
        return await self.vector_store.query_similar(text, k)

    @classmethod
    async def validate_config(cls, config: Dict) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
