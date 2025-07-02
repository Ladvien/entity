from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from pipeline.base_plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class VectorStore(ABC):
    """Interface for vector store backends."""

    @abstractmethod
    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        """Add ``text`` and optional ``metadata`` to the store."""

    @abstractmethod
    async def query_similar(self, query: str, k: int) -> List[str]:
        """Return the ``k`` most similar items for ``query``."""


class VectorStoreResource(ResourcePlugin, VectorStore, ABC):
    """Base class for vector store resources."""

    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None
