from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Set, cast

from .registries import SystemRegistries


class PipelineManager:
    """Manage concurrent pipeline executions and track active pipelines.

    Ensures **Linear Pipeline Flow (23)** by coordinating stage execution
    across multiple requests.
    """

    def __init__(self, registries: Optional[SystemRegistries] = None) -> None:
        self._registries = registries
        self._tasks: Set[asyncio.Task] = set()
        self._active: Set[str] = set()
        self._lock = asyncio.Lock()

    def start_pipeline(self, message: str) -> asyncio.Task:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        task = loop.create_task(self._run_pipeline(message))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def register(self, pipeline_id: str) -> None:
        async with self._lock:
            self._active.add(pipeline_id)

    async def deregister(self, pipeline_id: str) -> None:
        async with self._lock:
            self._active.discard(pipeline_id)

    async def _run_pipeline(self, message: str) -> Dict[str, Any]:
        if self._registries is None:
            raise ValueError("PipelineManager requires registries to run pipelines")
        from .execution import execute_pipeline

        result = await execute_pipeline(
            message, self._registries, pipeline_manager=self
        )
        return cast(Dict[str, Any], result)

    async def run_pipeline(self, message: str) -> Dict[str, Any]:
        return await self._run_pipeline(message)

    async def has_active_pipelines_async(self) -> bool:
        async with self._lock:
            self._tasks = {t for t in self._tasks if not t.done()}
            return bool(self._tasks or self._active)

    def has_active_pipelines(self) -> bool:
        self._tasks = {t for t in self._tasks if not t.done()}
        return bool(self._tasks or self._active)
