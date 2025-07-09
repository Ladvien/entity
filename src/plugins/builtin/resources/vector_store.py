from __future__ import annotations

"""Interface for vector store backends."""
from abc import ABC, abstractmethod
from typing import Dict, List

from .base import BaseResource


class VectorStore(ABC):
    """Interface for vector store backends."""

    @abstractmethod
    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        """Persist ``text`` along with optional ``metadata`` as an embedding."""

    @abstractmethod
    async def query_similar(self, query: str, k: int) -> List[str]:
        """Return the ``k`` most similar items for ``query``."""


class VectorStoreResource(BaseResource, VectorStore, ABC):
    """Base class for vector store resources."""

    dependencies: list[str] = []
