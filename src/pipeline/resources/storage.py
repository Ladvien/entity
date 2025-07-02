from __future__ import annotations

from typing import List, Protocol

from pipeline.context import ConversationEntry


class StorageBackend(Protocol):
    """Protocol for resources that persist conversation history."""

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None: ...

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]: ...
