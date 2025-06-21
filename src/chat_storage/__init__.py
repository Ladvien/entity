# src/storage/__init__.py - FIXED VERSION

from typing import TYPE_CHECKING
from src.service.config import StorageConfig, DatabaseConfig
from src.chat_storage.base_chat_storage import BaseChatStorage
from src.chat_storage.postgres_chat_storage import PostgresChatStorage
from src.db.connection import DatabaseConnection

if TYPE_CHECKING:
    from src.shared.models import ChatInteraction


async def create_storage(
    storage_config: StorageConfig, database_config: DatabaseConfig
) -> BaseChatStorage:
    """
    Factory function to create storage instances using centralized DB connection

    Args:
        storage_config: Storage configuration (backend type, table names, etc.)
        database_config: Database configuration

    Returns:
        BaseChatStorage: Configured storage instance
    """
    backend = storage_config.backend.lower()

    if backend == "postgres" or backend == "postgresql":
        # Create centralized database connection
        db_connection = DatabaseConnection.from_config(database_config)

        # Test the connection
        if not await db_connection.test_connection():
            raise ConnectionError("Failed to connect to database")

        # Ensure schema exists
        if not await db_connection.ensure_schema():
            raise RuntimeError(f"Failed to ensure schema '{db_connection.schema}'")

        # Create storage with centralized connection
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


# Legacy factory for backward compatibility (DEPRECATED)
async def create_storage_legacy(storage_config: StorageConfig, db_config):
    """
    Legacy factory - DEPRECATED
    Use create_storage() instead
    """
    import warnings

    warnings.warn(
        "create_storage_legacy is deprecated. Use create_storage() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if isinstance(db_config, dict):
        db_config = DatabaseConfig(**db_config)

    return await create_storage(storage_config, db_config)


# Make imports available at package level
__all__ = [
    "create_storage",
    "create_storage_legacy",  # Deprecated
    "BaseChatStorage",
    "PostgresChatStorage",
    "DatabaseConnection",
]
