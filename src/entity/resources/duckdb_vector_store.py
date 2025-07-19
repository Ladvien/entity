from __future__ import annotations

from typing import Dict, List

from entity.pipeline.errors import ResourceInitializationError
from entity.infrastructure.duckdb_vector import DuckDBVectorInfrastructure

from .vector_store import VectorStoreResource


class DuckDBVectorStore(VectorStoreResource):
    """Simple vector store using a DuckDB table.

    This implementation stores text alongside a naive numeric embedding and
    performs similarity search using cosine distance. The embedding is derived
    from the UTF-8 code points of the text and is only intended as a minimal
    placeholder for real embeddings.
    """

    name = "duckdb_vector_store"
    infrastructure_dependencies = ["vector_store_backend"]
    resource_category = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.vector_store_backend: DuckDBVectorInfrastructure | None = None

    async def initialize(self) -> None:
        if self.vector_store_backend is None:
            raise ResourceInitializationError(
                "Vector store backend not injected", self.name
            )
        self._pool = self.vector_store_backend.get_connection_pool()

    async def add_embedding(self, text: str) -> None:
        if self.vector_store_backend is not None:
            await self.vector_store_backend.add_embedding(text)

    async def query_similar(self, query: str, k: int = 5) -> List[str]:
        if self.vector_store_backend is None:
            return []
        return await self.vector_store_backend.query_similar(query, k)


__all__ = ["DuckDBVectorStore"]
