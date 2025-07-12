"""Unified Memory resource."""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime
import json
import inspect

from .base import AgentResource
from ..core.plugins import ValidationResult
from ..core.state import ConversationEntry


class Conversation:
    """Simple conversation helper used by tests."""

    def __init__(self, capabilities: SystemRegistries) -> None:
        self._caps = capabilities

    async def process_request(self, message: str) -> Any:
        result = await execute_pipeline(message, self._caps)
        while isinstance(result, dict) and result.get("type") == "continue_processing":
            next_msg = result.get("message", "")
            result = await execute_pipeline(next_msg, self._caps)
        return result


def _normalize_args(args: tuple[Any, ...]) -> Any:
    if not args:
        return ()
    if len(args) == 1 and not isinstance(args[0], (list, tuple, dict)):
        return (args[0],)
    return args


async def _exec(conn: Any, query: str, *args: Any) -> Any:
    """Execute query supporting sync or async connections."""
    fn = getattr(conn, "execute", None)
    if fn is None:
        return None
    params = _normalize_args(args)
    result = fn(query, params)
    if inspect.isawaitable(result):
        result = await result
    return result


async def _fetchall(conn: Any, query: str, *args: Any) -> List[Any]:
    """Fetch all rows from the given query."""
    params = _normalize_args(args)
    if hasattr(conn, "fetch"):
        result = conn.fetch(query, params)
        if inspect.isawaitable(result):
            result = await result
        return list(result)
    result = conn.execute(query, params)
    if inspect.isawaitable(result):
        result = await result
    if hasattr(result, "fetchall"):
        rows = result.fetchall()
        if inspect.isawaitable(rows):
            rows = await rows
        return list(rows)
    return []


class Memory(AgentResource):
    """Store key/value pairs, conversation history, and vectors."""

    name = "memory"
    dependencies: list[str] = ["database", "vector_store"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._kv: Dict[str, Any] = {}
        self._conversations: Dict[str, List[ConversationEntry]] = {}
        self._vectors: Dict[str, List[float]] = {}
        self.database = None
        self.vector_store = None

    async def _execute_impl(self, context: Any) -> None:  # noqa: D401, ARG002
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------
    async def get(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from persistent storage or ``default`` when missing."""
        table = self.database.config.get("kv_table", "memory_kv")
        async with self.database.connection() as conn:
            rows = await _fetchall(
                conn,
                f"SELECT value FROM {table} WHERE key = ?",
                key,
            )
        if not rows:
            return default
        value = rows[0][0] if not isinstance(rows[0], dict) else rows[0].get("value")
        try:
            return json.loads(value)
        except Exception:
            return value

    async def set(self, key: str, value: Any) -> None:
        """Persist ``value`` for later retrieval."""
        table = self.database.config.get("kv_table", "memory_kv")
        payload = json.dumps(value)
        async with self.database.connection() as conn:
            await _exec(conn, f"DELETE FROM {table} WHERE key = ?", key)
            await _exec(conn, f"INSERT INTO {table} VALUES (?, ?)", key, payload)

    # Backwards compatibility
    remember = set

    async def clear(self) -> None:
        table = self.database.config.get("kv_table", "memory_kv")
        async with self.database.connection() as conn:
            await _exec(conn, f"DELETE FROM {table}")

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        table = self.database.config.get("history_table", "conversation_history")
        async with self.database.connection() as conn:
            await _exec(
                conn,
                f"DELETE FROM {table} WHERE conversation_id = ?",
                conversation_id,
            )
            for entry in history:
                await _exec(
                    conn,
                    f"INSERT INTO {table} VALUES (?, ?, ?, ?, ?)",
                    conversation_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp.isoformat(),
                )

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        table = self.database.config.get("history_table", "conversation_history")
        async with self.database.connection() as conn:
            rows = await _fetchall(
                conn,
                f"SELECT role, content, metadata, timestamp FROM {table} WHERE conversation_id = ? ORDER BY timestamp",
                conversation_id,
            )
        result: List[ConversationEntry] = []
        for row in rows:
            role = row[0] if not isinstance(row, dict) else row["role"]
            content = row[1] if not isinstance(row, dict) else row["content"]
            metadata = row[2] if not isinstance(row, dict) else row.get("metadata", {})
            timestamp = row[3] if not isinstance(row, dict) else row["timestamp"]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            result.append(
                ConversationEntry(
                    content=content,
                    role=role,
                    timestamp=timestamp,
                    metadata=metadata,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Vector helpers
    # ------------------------------------------------------------------
    async def add_embedding(self, text: str) -> None:
        await self.vector_store.add_embedding(text)

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        return await self.vector_store.query_similar(query, k)

    @classmethod
    async def validate_config(cls, config: Dict) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
