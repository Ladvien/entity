"""Unified Memory resource."""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime
import json
import inspect

from .base import AgentResource
from ..core.plugins import ValidationResult
from ..core.state import ConversationEntry
from ..core.resources.container import ResourcePool


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

    def __init__(
        self,
        database: DatabaseInterface | None = None,
        vector_store: VectorStoreInterface | None = None,
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.database = database
        self.vector_store = vector_store
        self._kv: Dict[str, Any] = {}
        self._conversations: Dict[str, List[ConversationEntry]] = {}
        self._vectors: Dict[str, List[float]] = {}
        self._pool: ResourcePool | None = (
            database.get_connection_pool() if database is not None else None
        )

    async def initialize(self) -> None:
        if self._pool is None and self.database is not None:
            self._pool = self.database.get_connection_pool()

    async def _execute_impl(self, context: Any) -> None:  # noqa: D401, ARG002
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from memory or ``default`` when missing."""
        if self.database is not None:
            table = self.database.config.get("kv_table", "kv_store")

            async def _get() -> Any:
                async with self._pool as conn:
                    rows = await _fetchall(
                        conn,
                        f"SELECT value FROM {table} WHERE key = ?",
                        key,
                    )
                if not rows:
                    return default
                value = (
                    rows[0][0] if not isinstance(rows[0], dict) else rows[0]["value"]
                )
                try:
                    return json.loads(value)
                except Exception:
                    return value

            return asyncio.get_event_loop().run_until_complete(_get())
        return self._kv.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` for later retrieval."""
        if self.database is not None:
            table = self.database.config.get("kv_table", "kv_store")

            async def _set() -> None:
                async with self._pool as conn:
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
        self._kv[key] = value

    # Backwards compatibility
    remember = set

    def clear(self) -> None:
        if self.database is not None:
            table = self.database.config.get("kv_table", "kv_store")

            async def _clear() -> None:
                async with self._pool as conn:
                    await _exec(conn, f"DELETE FROM {table}")

            asyncio.get_event_loop().run_until_complete(_clear())
            return None
        self._kv.clear()

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self.database is not None:
            table = self.database.config.get("history_table", "conversation_history")
            async with self._pool as conn:
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
        if self.database is not None:
            table = self.database.config.get("history_table", "conversation_history")
            async with self._pool as conn:
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
    async def add_embedding(self, text: str) -> None:
        await self.vector_store.add_embedding(text)

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        return await self.vector_store.query_similar(query, k)

    async def validate_runtime(self) -> ValidationResult:
        """Check dependencies for availability."""
        if hasattr(self, "database") and hasattr(self.database, "validate_runtime"):
            result = await self.database.validate_runtime()
            if not result.success:
                return ValidationResult.error_result(f"database: {result.message}")
        if hasattr(self, "vector_store") and hasattr(
            self.vector_store, "validate_runtime"
        ):
            result = await self.vector_store.validate_runtime()
            if not result.success:
                return ValidationResult.error_result(f"vector_store: {result.message}")
        return ValidationResult.success_result()

    @classmethod
    async def validate_config(cls, config: Dict) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
