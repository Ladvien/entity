# src/storage/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.shared.models import ChatInteraction


class BaseChatStorage(ABC):
    """Base class for chat storage implementations"""

    @abstractmethod
    async def save_interaction(self, interaction: ChatInteraction):
        """Save a ChatInteraction to storage"""
        pass

    @abstractmethod
    async def get_history(
        self, thread_id: str, limit: int = 100
    ) -> List[ChatInteraction]:
        """Get chat history as list of ChatInteraction objects"""
        pass

    # Legacy methods for backward compatibility
    async def save_interaction_legacy(
        self,
        thread_id: str,
        user_input: str,
        agent_output: str,
        metadata: Dict[str, Any],
    ):
        """Legacy save method - should be implemented by subclasses if needed"""
        raise NotImplementedError("Legacy save method not implemented")

    async def get_history_legacy(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Legacy get_history method - should be implemented by subclasses if needed"""
        raise NotImplementedError("Legacy get_history method not implemented")
