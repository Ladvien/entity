from abc import ABC, abstractmethod
from typing import Dict, Any
from src.service.config import DatabaseConfig, StorageConfig
from src.storage.postgres import PostgresChatStorage


async def create_storage(storage_config: StorageConfig, db_config: DatabaseConfig):
    storage = PostgresChatStorage(db_config, storage_config)
    await storage.initialize()
    return storage


class ChatStorage(ABC):
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
