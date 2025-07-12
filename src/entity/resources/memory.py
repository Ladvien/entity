"""Unified Memory resource without in-memory state."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
import json

from .base import AgentResource
from .interfaces.database import DatabaseResource as DatabaseInterface
from .interfaces.vector_store import (
    VectorStoreResource as VectorStoreInterface,
)
from ..core.plugins import ValidationResult
from ..core.state import ConversationEntry
from pipeline.errors import InitializationError, ResourceInitializationError


class Memory(AgentResource):
    """Persist conversations, key/value pairs and vectors."""

    name = "memory"
    dependencies = ["database", "vector_store?"]

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.database: DatabaseInterface | None = None
        self.vector_store: VectorStoreInterface | None = None
        self._pool: Any | None = None
        self._kv_table = self.config.get("kv_table", "memory_kv")
        self._history_table = self.config.get("history_table", "conversation_history")

    async def initialize(self) -> None:
        if self.database is None:
            raise ResourceInitializationError("Database dependency not injected")
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
    async def get(self, key: str, default: Any | None = None) -> Any:
        return await self.fetch_persistent(key, default)

    async def set(self, key: str, value: Any) -> None:
        await self.store_persistent(key, value)

    # ``store_persistent`` and ``fetch_persistent`` are implemented below.

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
        return await self.vector_search(text, k)

    @classmethod
    async def validate_config(
        cls, config: Dict[str, Any]
    ) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()

    # ------------------------------------------------------------------
    # Advanced operations
    # ------------------------------------------------------------------

    async def query(self, sql: str, params: List | None = None) -> List[Dict[str, Any]]:
        """Execute ``sql`` using the injected database."""
        if self._pool is None:
            raise InitializationError("Database dependency not injected")

        cursor = self._pool.execute(sql, params or [])
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    async def vector_search(self, query: str, k: int = 5) -> List[str]:
        """Delegate semantic search to the vector store."""
        if self.vector_store is None:
            return []
        return await self.vector_store.query_similar(query, k)

    async def batch_store(self, key_value_pairs: Dict[str, Any]) -> None:
        """Store multiple key/value pairs efficiently."""
        if self._pool is None:
            return
        rows = [(key, json.dumps(value)) for key, value in key_value_pairs.items()]
        self._pool.executemany(
            f"INSERT OR REPLACE INTO {self._kv_table} VALUES (?, ?)", rows
        )

    async def store_persistent(self, key: str, value: Any) -> None:
        """Persist ``value`` under ``key``."""
        if self._pool is None:
            return
        self._pool.execute(
            f"INSERT OR REPLACE INTO {self._kv_table} VALUES (?, ?)",
            (key, json.dumps(value)),
        )

    async def fetch_persistent(self, key: str, default: Any = None) -> Any:
        """Retrieve a persisted value."""
        if self._pool is None:
            return default
        row = self._pool.execute(
            f"SELECT value FROM {self._kv_table} WHERE key = ?",
            (key,),
        ).fetchone()
        return json.loads(row[0]) if row else default

    async def delete_persistent(self, key: str) -> None:
        """Remove ``key`` from persistent storage."""
        if self._pool is None:
            return
        self._pool.execute(
            f"DELETE FROM {self._kv_table} WHERE key = ?",
            (key,),
        )

    async def add_conversation_entry(
        self, conversation_id: str, entry: ConversationEntry
    ) -> None:
        """Append a single entry to ``conversation_id``."""
        if self._pool is None:
            return
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

    async def conversation_search(
        self, query: str, user_id: str | None = None, days: int | None = None
    ) -> List[Dict[str, Any]]:
        """Search conversation history using simple text matching."""
        if self._pool is None:
            return []

        sql = (
            f"SELECT conversation_id, role, content, metadata, timestamp "
            f"FROM {self._history_table}"
        )
        clauses = []
        params: List[Any] = []
        if user_id:
            clauses.append("conversation_id LIKE ?")
            params.append(f"{user_id}%")
        if days is not None:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            clauses.append("timestamp >= ?")
            params.append(since)
        if query:
            clauses.append("content LIKE ?")
            params.append(f"%{query}%")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY timestamp DESC"

        rows = self._pool.execute(sql, params).fetchall()
        return [
            {
                "conversation_id": row[0],
                "role": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "timestamp": row[4],
            }
            for row in rows
        ]

    async def conversation_statistics(self, user_id: str) -> Dict[str, Any]:
        """Return simple statistics for a user's conversations."""
        if self._pool is None:
            return {}
        conv_rows = self._pool.execute(
            f"SELECT DISTINCT conversation_id FROM {self._history_table} "
            "WHERE conversation_id LIKE ?",
            (f"{user_id}%",),
        ).fetchall()
        total_messages = self._pool.execute(
            f"SELECT COUNT(*) FROM {self._history_table} WHERE conversation_id LIKE ?",
            (f"{user_id}%",),
        ).fetchone()[0]
        return {
            "conversations": len(conv_rows),
            "messages": total_messages,
        }

    # ------------------------------------------------------------------
    # Backwards compatibility
    # ------------------------------------------------------------------

    remember = store_persistent
