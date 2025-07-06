from __future__ import annotations

"""Memory resource interface."""
from abc import ABC, abstractmethod
from typing import Any, List

from pipeline.state import ConversationEntry


class Memory(ABC):
    """Interface for memory storage resources."""

    async def initialize(self) -> None:  # pragma: no cover - optional
        """Optional async initialization hook."""
        return None

    @abstractmethod
    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from memory."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` in memory under ``key``."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all values from memory."""

    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        """Persist conversation ``history`` if supported."""
        return None

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        """Retrieve stored conversation for ``conversation_id`` if available."""
        return []

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        """Return semantically similar text results if supported."""
        return []
