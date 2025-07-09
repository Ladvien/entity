from __future__ import annotations

"""In-memory vector store resource."""

from typing import Dict, List, Tuple

from plugins.builtin.resources.vector_store import VectorStoreResource


class MemoryVectorStore(VectorStoreResource):
    """Persist embeddings in memory and provide similarity search."""

    name = "vector_memory"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._dim = int(self.config.get("dimensions", 3))
        self._items: List[Tuple[str, List[float]]] = []

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self._dim
        for i, byte in enumerate(text.encode("utf-8")):
            values[i % self._dim] += float(byte)
        return [v / 255.0 for v in values]

    async def add_embedding(self, text: str, metadata: Dict | None = None) -> None:
        self._items.append((text, self._embed(text)))

    async def query_similar(self, query: str, k: int) -> List[str]:
        if not self._items:
            return []
        target = self._embed(query)

        def sim(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(y * y for y in b) ** 0.5
            return dot / (norm_a * norm_b + 1e-9)

        scored = sorted(
            self._items,
            key=lambda item: sim(item[1], target),
            reverse=True,
        )
        return [text for text, _ in scored[:k]]
