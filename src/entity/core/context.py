from __future__ import annotations

"""Minimal plugin context objects."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ConversationEntry:
    content: str
    role: str
    metadata: Dict[str, Any] | None = None


class PluginContext:
    """Simplified context passed to plugins."""

    def __init__(self) -> None:
        self._history: List[ConversationEntry] = []
        self._store: Dict[str, Any] = {}
        self.response: Any | None = None

    def get_conversation_history(self) -> List[ConversationEntry]:
        return list(self._history)

    async def call_llm(self, _context: Any, _prompt: str, *, purpose: str = ""):
        class _Resp:
            content = ""

        return _Resp()

    def add_conversation_entry(
        self, *, content: str, role: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        self._history.append(ConversationEntry(content, role, metadata or {}))

    async def tool_use(self, name: str, **params: Any) -> None:  # noqa: ARG002
        return None

    def store(self, key: str, value: Any) -> None:
        self._store[key] = value

    def load(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from the internal store or ``default`` when missing."""

        return self._store.get(key, default)

    def has(self, key: str) -> bool:
        """Return ``True`` when ``key`` is stored."""

        return key in self._store

    def set_response(self, value: Any) -> None:
        self.response = value
