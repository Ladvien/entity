from __future__ import annotations

"""Unified Memory resource."""

from math import sqrt
from typing import Any, Dict, Iterable, List

from entity.core.registries import SystemRegistries
from pipeline.pipeline import execute_pipeline

from ..core.plugins import ResourcePlugin, ValidationResult
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


def _cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    denom_a = sqrt(sum(x * x for x in a))
    denom_b = sqrt(sum(y * y for y in b))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return num / (denom_a * denom_b)


class ConversationHistory:
    """Helper managing conversation histories."""

    def __init__(self, store: Dict[str, List[ConversationEntry]]) -> None:
        self._store = store

    async def save(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        self._store[conversation_id] = list(history)

    async def load(self, conversation_id: str) -> List[ConversationEntry]:
        return list(self._store.get(conversation_id, []))


class Memory(ResourcePlugin):
    """Store key/value pairs, conversation history, and vectors."""

    name = "memory"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._kv: Dict[str, Any] = {}
        self._conversations: Dict[str, List[ConversationEntry]] = {}
        self._vectors: Dict[str, List[float]] = {}
        self._history = ConversationHistory(self._conversations)
        self.database: Any | None = None
        self.vector_store: Any | None = None

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
        await self._history.save(conversation_id, history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        return await self._history.load(conversation_id)

    @property
    def conversation_history(self) -> ConversationHistory:
        """Return the conversation history manager."""
        return self._history

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

    # ------------------------------------------------------------------
    # Conversation manager
    # ------------------------------------------------------------------
    def start_conversation(self, capabilities: SystemRegistries) -> Conversation:
        return Conversation(capabilities)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:  # noqa: D401
        return ValidationResult.success_result()
