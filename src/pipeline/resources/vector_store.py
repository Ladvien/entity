from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class VectorStoreResource(ABC):
    """Abstract interface for vector store resources."""

    @abstractmethod
    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        """Persist ``text`` embedding with optional ``metadata``."""

    @abstractmethod
    async def query_similar(self, query: str, k: int) -> List[Dict]:
        """Return top ``k`` items most similar to ``query``."""
