# entity_service/storage/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any


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
