"""Unified Memory resource without in-memory state."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
import inspect
import json

from .base import AgentResource
from .interfaces.database import DatabaseResource as DatabaseInterface
from .interfaces.vector_store import (
    VectorStoreResource as VectorStoreInterface,
)
from ..core.resources.container import ResourcePool
from ..core.plugins import ValidationResult
from entity.config.models import MemoryConfig
from pydantic import ValidationError
from ..core.state import ConversationEntry
from entity.pipeline.errors import InitializationError, ResourceInitializationError


class Memory(AgentResource):
    """Persist conversations, key/value pairs and vectors."""

    name = "memory"
    dependencies = ["database", "vector_store?"]
    resource_category = "database"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.database: DatabaseInterface | None = None
        self.vector_store: VectorStoreInterface | None = None
        self._pool: ResourcePool | None = None
        self._kv_table = self.config.get("kv_table", "memory_kv")
        self._history_table = self.config.get("history_table", "conversation_history")

    def _maybe_commit(self, conn: Any) -> None:
        """Commit writes when supported by the connection."""
        commit = getattr(conn, "commit", None)
        if callable(commit):
            commit()

    async def initialize(self) -> None:
        if self.database is None:
            raise ResourceInitializationError(
                "Database dependency not injected", self.name
            )
        self._pool = self.database.get_connection_pool()
        async with self.database.connection() as conn:
            await _execute(
                conn,
                f"CREATE TABLE IF NOT EXISTS {self._kv_table} (key TEXT PRIMARY KEY, value TEXT)",
            )
            await _execute(
                conn,
                f"CREATE TABLE IF NOT EXISTS {self._history_table} ("
                "conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)",
            )
            self._maybe_commit(conn)

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------
    async def get(
        self, key: str, default: Any | None = None, *, user_id: str = "default"
    ) -> Any:
        return await self.fetch_persistent(key, default, user_id=user_id)

    async def set(self, key: str, value: Any, *, user_id: str = "default") -> None:
        await self.store_persistent(key, value, user_id=user_id)

    # ``store_persistent`` and ``fetch_persistent`` are implemented below.

    async def clear(self) -> None:
        if self.database is None:
            return
        async with self.database.connection() as conn:
            await _execute(conn, f"DELETE FROM {self._kv_table}")
            self._maybe_commit(conn)

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    async def save_conversation(
        self,
        pipeline_id: str,
        history: List[ConversationEntry],
        *,
        user_id: str = "default",
    ) -> None:
        conversation_id = f"{user_id}_{pipeline_id}"
        if self._pool is None:
            return
        async with self.database.connection() as conn:
            await _execute(
                conn,
                f"DELETE FROM {self._history_table} WHERE conversation_id = ?",
                (conversation_id,),
            )
            for entry in history:
                await _execute(
                    conn,
                    f"INSERT INTO {self._history_table} VALUES (?, ?, ?, ?, ?)",
                    (
                        conversation_id,
                        entry.role,
                        entry.content,
                        json.dumps(entry.metadata),
                        entry.timestamp.isoformat(),
                    ),
                )
            self._maybe_commit(conn)

    async def load_conversation(
        self, pipeline_id: str, *, user_id: str = "default"
    ) -> List[ConversationEntry]:
        conversation_id = f"{user_id}_{pipeline_id}"
        if self.database is None:
            return []
        async with self.database.connection() as conn:
            cursor = await _execute(
                conn,
                f"SELECT role, content, metadata, timestamp FROM {self._history_table} "
                "WHERE conversation_id = ? ORDER BY timestamp",
                (conversation_id,),
            )
            rows = await _maybe_await(cursor.fetchall())
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
        try:
            MemoryConfig.parse_obj(config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    # ------------------------------------------------------------------
    # Advanced operations
    # ------------------------------------------------------------------

    async def query(self, sql: str, params: List | None = None) -> List[Dict[str, Any]]:
        """Execute ``sql`` using the injected database."""
        if self._pool is None:
            raise InitializationError("Database dependency not injected")

        async with self.database.connection() as conn:
            cursor = await _execute(conn, sql, params)
            columns = [d[0] for d in cursor.description]
            rows = await _maybe_await(cursor.fetchall())
            return [dict(zip(columns, row)) for row in rows]

    async def vector_search(self, query: str, k: int = 5) -> List[str]:
        """Delegate semantic search to the vector store."""
        if self.vector_store is None:
            return []
        return await self.vector_store.query_similar(query, k)

    async def batch_store(
        self, key_value_pairs: Dict[str, Any], *, user_id: str = "default"
    ) -> None:
        """Store multiple key/value pairs efficiently."""
        if self._pool is None:
            return
        rows = [
            (f"{user_id}:{key}", json.dumps(value))
            for key, value in key_value_pairs.items()
        ]
        async with self.database.connection() as conn:
            conn.executemany(
                f"INSERT OR REPLACE INTO {self._kv_table} VALUES (?, ?)", rows
            )
            self._maybe_commit(conn)

    async def store_persistent(
        self, key: str, value: Any, *, user_id: str = "default"
    ) -> None:
        """Persist ``value`` under ``key``."""
        if self._pool is None:
            return
        namespaced_key = f"{user_id}:{key}"
        async with self.database.connection() as conn:
            await _execute(
                conn,
                f"INSERT OR REPLACE INTO {self._kv_table} VALUES (?, ?)",
                (namespaced_key, json.dumps(value)),
            )
            self._maybe_commit(conn)

    async def fetch_persistent(
        self, key: str, default: Any = None, *, user_id: str = "default"
    ) -> Any:
        """Retrieve a persisted value."""
        if self._pool is None:
            return default
        namespaced_key = f"{user_id}:{key}"
        async with self.database.connection() as conn:
            cursor = await _execute(
                conn,
                f"SELECT value FROM {self._kv_table} WHERE key = ?",
                (namespaced_key,),
            )
            row = await _maybe_await(cursor.fetchone())
        return json.loads(row[0]) if row else default

    async def delete_persistent(self, key: str, *, user_id: str = "default") -> None:
        """Remove ``key`` from persistent storage."""
        if self._pool is None:
            return
        namespaced_key = f"{user_id}:{key}"
        async with self.database.connection() as conn:
            await _execute(
                conn,
                f"DELETE FROM {self._kv_table} WHERE key = ?",
                (namespaced_key,),
            )
            self._maybe_commit(conn)

    async def add_conversation_entry(
        self, pipeline_id: str, entry: ConversationEntry, *, user_id: str = "default"
    ) -> None:
        conversation_id = f"{user_id}_{pipeline_id}"
        """Append a single entry to ``conversation_id``."""
        if self._pool is None:
            return
        async with self.database.connection() as conn:
            await _execute(
                conn,
                f"INSERT INTO {self._history_table} VALUES (?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp.isoformat(),
                ),
            )
            self._maybe_commit(conn)
        if self.vector_store is not None:
            await self.vector_store.add_embedding(entry.content)

    async def conversation_search(
        self,
        query: str,
        user_id: str | None = None,
        days: int | None = None,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search conversation history using vector similarity when possible."""
        if self._pool is None:
            return []
        sql = (
            f"SELECT conversation_id, role, content, metadata, timestamp "
            f"FROM {self._history_table}"
        )
        clauses: List[str] = []
        params: List[Any] = []

        if user_id:
            clauses.append("conversation_id LIKE ?")
            params.append(f"{user_id}%")
        if days is not None:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            clauses.append("timestamp >= ?")
            params.append(since)

        if query:
            if self.vector_store is not None:
                similar = await self.vector_store.query_similar(query, k)
                if not similar:
                    return []
                placeholders = ", ".join("?" for _ in similar)
                clauses.append(f"content IN ({placeholders})")
                params.extend(similar)
            else:
                clauses.append("content LIKE ?")
                params.append(f"%{query}%")

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY timestamp DESC"

        async with self.database.connection() as conn:
            cursor = await _execute(conn, sql, params)
            rows = await _maybe_await(cursor.fetchall())
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
        """Return metrics for all conversations belonging to ``user_id``."""
        if self._pool is None:
            return {}

        async with self.database.connection() as conn:
            cursor = await _execute(
                conn,
                f"SELECT conversation_id, content, timestamp FROM {self._history_table} "
                "WHERE conversation_id LIKE ? ORDER BY timestamp",
                (f"{user_id}%",),
            )
            rows = await _maybe_await(cursor.fetchall())

        conv_ids: set[str] = set()
        total_length = 0
        last_activity: datetime | None = None

        for conv_id, content, ts in rows:
            conv_ids.add(conv_id)
            total_length += len(content)
            timestamp = datetime.fromisoformat(ts)
            last_activity = (
                max(last_activity, timestamp) if last_activity else timestamp
            )

        total_messages = len(rows)
        conversations = len(conv_ids)
        average_length = total_length / total_messages if total_messages else 0

        return {
            "conversations": conversations,
            "messages": total_messages,
            "average_length": average_length,
            "last_activity": last_activity.isoformat() if last_activity else None,
        }

    # ------------------------------------------------------------------
    # Backwards compatibility
    # ------------------------------------------------------------------

    remember = store_persistent
    recall = fetch_persistent
    forget = delete_persistent


async def _execute(conn: Any, sql: str, params: Any | None = None) -> Any:
    """Run a query and await the result when necessary."""
    result = conn.execute(sql, params or [])
    if inspect.isawaitable(result):
        result = await result
    return result


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value
