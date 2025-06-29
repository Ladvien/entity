from __future__ import annotations

from asyncio import Lock


class PipelineManager:
    """Track running pipelines for safe configuration updates."""

    def __init__(self) -> None:
        self._active: set[str] = set()
        self._lock = Lock()

    async def register(self, pipeline_id: str) -> None:
        async with self._lock:
            self._active.add(pipeline_id)

    async def deregister(self, pipeline_id: str) -> None:
        async with self._lock:
            self._active.discard(pipeline_id)

    async def has_active_pipelines(self) -> bool:
        async with self._lock:
            return bool(self._active)
