from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from pipeline.resources.base import BaseResource


class VectorStore(ABC):
    """Interface for vector store backends."""

    @abstractmethod
    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        """Add ``text`` and optional ``metadata`` to the store."""

    @abstractmethod
    async def query_similar(self, query: str, k: int) -> List[str]:
        """Return the ``k`` most similar items for ``query``."""


class VectorStoreResource(BaseResource, VectorStore, ABC):
    """Base class for vector store resources."""
