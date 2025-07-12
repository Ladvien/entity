"""Unified Memory resource."""

from __future__ import annotations

from math import sqrt
from typing import Any, Dict, Iterable, List
from datetime import datetime
import json
import inspect

from .base import AgentResource
from .interfaces.database import DatabaseResource as DatabaseInterface
from .interfaces.vector_store import VectorStoreResource as VectorStoreInterface
from ..core.plugins import ValidationResult
from ..core.state import ConversationEntry


def _cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    denom_a = sqrt(sum(x * x for x in a))
    denom_b = sqrt(sum(y * y for y in b))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return num / (denom_a * denom_b)


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
        self.database = database
        self.vector_store = vector_store

    async def _execute_impl(self, context: Any) -> None:  # noqa: D401, ARG002
        return None

    # ------------------------------------------------------------------
    # Key-value helpers
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from memory or ``default`` when missing."""
        return self._kv.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` for later retrieval."""
        self._kv[key] = value

    # Backwards compatibility
    remember = set

    def clear(self) -> None:
        self._kv.clear()

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self.database is not None:
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
            return None
        self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        if self.database is not None:
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

    # ------------------------------------------------------------------
    # Vector helpers
    # ------------------------------------------------------------------
    async def add_embedding(self, key: str, vector: List[float]) -> None:
        self._vectors[key] = vector

    async def search_similar(self, vector: List[float], k: int = 5) -> List[str]:
        scores = {k_: _cosine_similarity(vector, v) for k_, v in self._vectors.items()}
        return [
            k
            for k, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[
                :k
            ]
        ]

    @classmethod
    async def validate_config(cls, config: Dict) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
