from __future__ import annotations

"""Minimal plugin context objects."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ConversationEntry:
    content: str
    role: str
    metadata: Dict[str, Any] | None = None


class PluginContext:
    """Simplified context passed to plugins with intuitive verbs."""

    def __init__(self, memory: Optional[Any] = None) -> None:
        self._history: List[ConversationEntry] = []
        self._cache: Dict[str, Any] = {}
        self._memory = memory
        self.response: Any | None = None

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------

    def conversation(self) -> List[ConversationEntry]:
        """Return the current conversation history."""
        return list(self._history)

    async def call_llm(self, _context: Any, _prompt: str, *, purpose: str = ""):
        class _Resp:
            content = ""

        return _Resp()

    def say(
        self,
        content: str,
        *,
        role: str = "assistant",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a message to the conversation history."""
        self._history.append(ConversationEntry(content, role, metadata or {}))

    async def tool_use(self, name: str, **params: Any) -> None:  # noqa: ARG002
        return None

    # ------------------------------------------------------------------
    # Temporary cache helpers
    # ------------------------------------------------------------------

    def cache(self, key: str, value: Any) -> None:
        """Store a temporary value for this pipeline run."""
        self._cache[key] = value

    def recall(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a cached value."""
        return self._cache.get(key, default)

    def has(self, key: str) -> bool:
        """Return True if ``key`` exists in the cache."""
        return key in self._cache

    # Backwards compatibility
    store = cache
    load = recall

    # ------------------------------------------------------------------
    # Persistent memory helpers
    # ------------------------------------------------------------------

    def remember(self, key: str, value: Any) -> None:
        """Persist ``value`` in the configured memory resource."""
        if self._memory is not None:
            self._memory.remember(key, value)

    def memory(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from persistent memory."""
        if self._memory is None:
            return default
        return self._memory.memory(key, default)

    def load(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from the internal store or ``default`` when missing."""

        return self._store.get(key, default)

    def has(self, key: str) -> bool:
        """Return ``True`` when ``key`` is stored."""

        return key in self._store

    def set_response(self, value: Any) -> None:
        self.response = value

    # Backwards compatibility
    get_conversation_history = conversation
    add_conversation_entry = say
