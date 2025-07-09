from __future__ import annotations

"""Compatibility wrapper delegating to :class:`AgentRuntime`."""

import asyncio
from typing import Generic, Optional, TypeVar, cast

from entity.core.runtime import AgentRuntime
from entity.core.state_logger import StateLogger
from registry import SystemRegistries

ResultT = TypeVar("ResultT")


class PipelineManager(Generic[ResultT]):
    """Backwards compatible manager interface."""

    def __init__(
        self,
        registries: Optional[SystemRegistries] = None,
        *,
        state_logger: StateLogger | None = None,
    ) -> None:
        self._runtime = AgentRuntime(registries, state_logger=state_logger)
        self._registries = self._runtime.registries

    # ------------------------------------------------------------------
    def start_pipeline(
        self, message: str, *, max_iterations: int = 5
    ) -> asyncio.Task[ResultT]:
        task = self._runtime.start_pipeline(message, max_iterations=max_iterations)
        return cast(asyncio.Task[ResultT], task)

    async def run_pipeline(self, message: str, *, max_iterations: int = 5) -> ResultT:
        result = await self._runtime.run_pipeline(
            message, max_iterations=max_iterations
        )
        return cast(ResultT, result)

    # Delegate activity tracking --------------------------------------
    async def register(self, pipeline_id: str) -> None:  # pragma: no cover - legacy
        await self._runtime.register(pipeline_id)

    async def deregister(self, pipeline_id: str) -> None:  # pragma: no cover - legacy
        await self._runtime.deregister(pipeline_id)

    async def has_active_pipelines_async(self) -> bool:
        return await self._runtime.has_active_pipelines_async()

    def has_active_pipelines(self) -> bool:
        return self._runtime.has_active_pipelines()

    async def active_pipeline_count_async(self) -> int:
        return await self._runtime.active_pipeline_count_async()

    def active_pipeline_count(self) -> int:
        return self._runtime.active_pipeline_count()
