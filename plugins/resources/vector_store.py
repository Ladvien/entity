from __future__ import annotations

from abc import ABC, abstractmethod


class VectorStoreResource(ABC):
    """Abstract interface for vector store backends."""

    @abstractmethod
    async def add_embedding(self, text: str, metadata: dict | None = None) -> None:
        """Persist ``text`` along with optional ``metadata`` as an embedding."""

    @abstractmethod
    async def query_similar(self, query: str, k: int) -> list[dict]:
        """Return the ``k`` most similar embeddings to ``query``."""
