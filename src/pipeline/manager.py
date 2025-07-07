from __future__ import annotations

import asyncio
from typing import Generic, Optional, Set, TypeVar, cast

from registry import SystemRegistries

from .state_logger import StateLogger

ResultT = TypeVar("ResultT")


class PipelineManager(Generic[ResultT]):
    """Manage concurrent pipeline executions and track active pipelines.

    Ensures **Linear Pipeline Flow (23)** by coordinating stage execution
    across multiple requests.
    """

    def __init__(
        self,
        registries: Optional[SystemRegistries] = None,
        *,
        state_logger: "StateLogger" | None = None,
    ) -> None:
        self._registries = registries
        self.state_logger = state_logger
        self._tasks: Set[asyncio.Task[ResultT]] = set()
        self._active: Set[str] = set()
        self._lock = asyncio.Lock()

    def start_pipeline(self, message: str) -> asyncio.Task[ResultT]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
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

    async def _run_pipeline(self, message: str) -> ResultT:
        if self._registries is None:
            raise ValueError("PipelineManager requires registries to run pipelines")
        from .pipeline import execute_pipeline

        result = await execute_pipeline(
            message,
            self._registries,
            pipeline_manager=self,
            state_logger=self.state_logger,
        )
        return cast(ResultT, result)

    async def run_pipeline(self, message: str) -> ResultT:
        return await self._run_pipeline(message)

    async def has_active_pipelines_async(self) -> bool:
        async with self._lock:
            self._tasks = {t for t in self._tasks if not t.done()}
            return bool(self._tasks or self._active)

    def has_active_pipelines(self) -> bool:
        self._tasks = {t for t in self._tasks if not t.done()}
        return bool(self._tasks or self._active)

    async def active_pipeline_count_async(self) -> int:
        """Return the number of pipelines currently executing."""
        async with self._lock:
            self._tasks = {t for t in self._tasks if not t.done()}
            return max(len(self._tasks), len(self._active))

    def active_pipeline_count(self) -> int:
        """Return the number of pipelines currently executing."""
        self._tasks = {t for t in self._tasks if not t.done()}
        return max(len(self._tasks), len(self._active))
