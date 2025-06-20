# src/storage/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.shared.models import ChatInteraction


class BaseChatStorage(ABC):
    """Abstract base class for chat storage implementations."""

    @abstractmethod
    async def save_interaction(self, interaction: ChatInteraction) -> None:
        """Save a ChatInteraction to the underlying storage."""
        pass

    @abstractmethod
    async def get_history(
        self, thread_id: str, limit: int = 100
    ) -> List[ChatInteraction]:
        """Retrieve chat history for a given thread."""
        pass

    @abstractmethod
    async def get_interaction_by_id(
        self, interaction_id: str
    ) -> Optional[ChatInteraction]:
        """Retrieve a single ChatInteraction by its interaction ID."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize storage (e.g. create schema or tables if needed)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any underlying connections/resources."""
        pass

    # Optional legacy methods for backward compatibility
    async def save_interaction_legacy(
        self,
        thread_id: str,
        user_input: str,
        agent_output: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Legacy method for saving interaction without full model."""
        raise NotImplementedError("Legacy save method not implemented")

    async def get_history_legacy(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Legacy method for retrieving raw chat history."""
        raise NotImplementedError("Legacy get_history method not implemented")
