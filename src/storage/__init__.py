# src/storage/__init__.py - Storage factory function

from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
from src.service.config import DatabaseConfig, StorageConfig
from src.storage.base import BaseChatStorage
from src.storage.postgres import PostgresChatStorage

if TYPE_CHECKING:
    from src.shared.models import ChatInteraction


async def create_storage(storage_config: StorageConfig, db_config: DatabaseConfig):
    """
    Factory function to create storage instances based on configuration

    Args:
        storage_config: Storage configuration (backend type, table names, etc.)
        db_config: Database configuration (connection details)

    Returns:
        BaseChatStorage: Configured storage instance
    """
    backend = storage_config.backend.lower()

    if backend == "postgres" or backend == "postgresql":
        storage = PostgresChatStorage(db_config, storage_config)
        await storage.initialize()
        return storage

    elif backend == "sqlite":
        # Future SQLite implementation
        raise NotImplementedError("SQLite storage not yet implemented")

    elif backend == "memory":
        # Future in-memory implementation
        raise NotImplementedError("In-memory storage not yet implemented")

    else:
        raise ValueError(f"Unsupported storage backend: {backend}")


class ChatStorage(ABC):
    """Legacy alias for BaseChatStorage - for backward compatibility"""

    @abstractmethod
    async def save_interaction(
        self,
        thread_id: str,
        user_input: str,
        agent_output: str,
        metadata: Dict[str, Any],
    ):
        pass

    @abstractmethod
    async def get_history(self, thread_id: str, limit: int = 100):
        pass


# Make imports available at package level
__all__ = ["create_storage", "BaseChatStorage", "ChatStorage", "PostgresChatStorage"]
