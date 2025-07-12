"""Unified Memory resource."""

from __future__ import annotations

from math import sqrt
from typing import Any, Dict, Iterable, List, cast
from datetime import datetime
import json
import inspect

from .base import AgentResource
from .interfaces.database import DatabaseResource as DatabaseInterface
from .interfaces.vector_store import (
    VectorStoreResource as VectorStoreInterface,
)
from ..core.plugins import ValidationResult
from ..core.state import ConversationEntry
from pipeline.errors import InitializationError


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


class Memory(AgentResource):  # type: ignore[misc]
    """Store key/value pairs, conversation history, and vectors."""

    name = "memory"
    dependencies: list[str] = ["database", "vector_store"]

    def __init__(
        self,
        database: DatabaseInterface | None = None,
        vector_store: VectorStoreInterface | None = None,
        config: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(config or {})
        self.database: DatabaseInterface | None = database
        self.vector_store: VectorStoreInterface | None = vector_store

    async def initialize(self) -> None:
        if self.database is None:
            raise InitializationError(
                self.name,
                "dependency injection",
                "Database dependency not injected.",
                kind="Resource",
            )
        if self.vector_store is None:
            raise InitializationError(
                self.name,
                "dependency injection",
                "Vector store dependency not injected.",
                kind="Resource",
            )
        assert self.database is not None
        assert self.vector_store is not None
        self.database = cast(DatabaseInterface, self.database)
        self.vector_store = cast(VectorStoreInterface, self.vector_store)

    async def _execute_impl(self, context: Any) -> None:  # noqa: D401, ARG002
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from memory or ``default`` when missing."""
        db = self.database
        assert db is not None
        table = db.config.get("kv_table", "kv_store")

        async def _get() -> Any:
            async with db.connection() as conn:
                rows = await _fetchall(
                    conn,
                    f"SELECT value FROM {table} WHERE key = ?",
                    key,
                )
            if not rows:
                return default
            value = rows[0][0] if not isinstance(rows[0], dict) else rows[0]["value"]
            try:
                return json.loads(value)
            except Exception:
                return value

        return asyncio.get_event_loop().run_until_complete(_get())

    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` for later retrieval."""
        db = self.database
        assert db is not None
        table = db.config.get("kv_table", "kv_store")

        async def _set() -> None:
            async with db.connection() as conn:
                await _exec(
                    conn,
                    f"DELETE FROM {table} WHERE key = ?",
                    key,
                )
                await _exec(
                    conn,
                    f"INSERT INTO {table} VALUES (?, ?)",
                    key,
                    json.dumps(value),
                )

        asyncio.get_event_loop().run_until_complete(_set())
        return None

    # Backwards compatibility
    remember = set

    def clear(self) -> None:
        db = self.database
        assert db is not None
        table = db.config.get("kv_table", "kv_store")

        async def _clear() -> None:
            async with db.connection() as conn:
                await _exec(conn, f"DELETE FROM {table}")

        asyncio.get_event_loop().run_until_complete(_clear())
        return None

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        db = self.database
        assert db is not None
        table = db.config.get("history_table", "conversation_history")
        async with db.connection() as conn:
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
        return None

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        db = self.database
        assert db is not None
        table = db.config.get("history_table", "conversation_history")
        async with db.connection() as conn:
            rows = await _fetchall(
                conn,
                f"SELECT role, content, metadata, timestamp FROM {table} WHERE conversation_id = ? ORDER BY timestamp",
                conversation_id,
            )
            result: List[ConversationEntry] = []
            for row in rows:
                role = row[0] if not isinstance(row, dict) else row["role"]
                content = row[1] if not isinstance(row, dict) else row["content"]
                metadata = (
                    row[2] if not isinstance(row, dict) else row.get("metadata", {})
                )
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
    async def add_embedding(self, key: str, vector: List[float]) -> None:
        db = self.database
        assert db is not None
        table = db.config.get("vector_table", "vectors")
        async with db.connection() as conn:
            await _exec(conn, f"DELETE FROM {table} WHERE key = ?", key)
            await _exec(
                conn, f"INSERT INTO {table} VALUES (?, ?)", key, json.dumps(vector)
            )

    async def search_similar(self, vector: List[float], k: int = 5) -> List[str]:
        db = self.database
        assert db is not None
        table = db.config.get("vector_table", "vectors")
        async with db.connection() as conn:
            rows = await _fetchall(conn, f"SELECT key, vector FROM {table}")
        scores: Dict[str, float] = {}
        for row in rows:
            key = row[0] if not isinstance(row, dict) else row["key"]
            val = row[1] if not isinstance(row, dict) else row["vector"]
            vec = json.loads(val) if isinstance(val, str) else val
            scores[key] = _cosine_similarity(vector, vec)
        return [
            item[0]
            for item in sorted(scores.items(), key=lambda it: it[1], reverse=True)[:k]
        ]

    @classmethod
    async def validate_config(
        cls, config: Dict[str, Any]
    ) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
