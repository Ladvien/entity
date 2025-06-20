# src/storage/__init__.py - Updated factory using DatabaseConnection

from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
from src.service.config import StorageConfig
from src.storage.base import BaseChatStorage
from src.storage.postgres import PostgresChatStorage
from src.db.connection import DatabaseConnection

if TYPE_CHECKING:
    from src.shared.models import ChatInteraction


async def create_storage(
    storage_config: StorageConfig, db_connection: DatabaseConnection
) -> BaseChatStorage:
    """
    Factory function to create storage instances using centralized DB connection

    Args:
        storage_config: Storage configuration (backend type, table names, etc.)
        db_connection: Centralized database connection instance

    Returns:
        BaseChatStorage: Configured storage instance
    """
    backend = storage_config.backend.lower()

    if backend == "postgres" or backend == "postgresql":
        storage = PostgresChatStorage(db_connection, storage_config)
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


# Keep the old factory for backward compatibility
async def create_storage_legacy(storage_config: StorageConfig, db_config):
    """
    Legacy factory that creates its own connection - for backward compatibility
    """
    from src.service.config import DatabaseConfig

    if isinstance(db_config, dict):
        db_config = DatabaseConfig(**db_config)

    # Create a temporary connection for this storage
    db_connection = DatabaseConnection.from_config(db_config)
    return await create_storage(storage_config, db_connection)


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
__all__ = [
    "create_storage",
    "create_storage_legacy",
    "BaseChatStorage",
    "ChatStorage",
    "PostgresChatStorage",
    "DatabaseConnection",
]
