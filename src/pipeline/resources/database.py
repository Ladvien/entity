from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from pipeline.context import ConversationEntry
from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class DatabaseResource(ResourcePlugin, ABC):
    """Abstract base class for database resources."""

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config)
        self.has_vector_store = False

    @abstractmethod
    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        """Persist conversation ``history``."""

    @abstractmethod
    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        """Retrieve stored history for ``conversation_id``."""
