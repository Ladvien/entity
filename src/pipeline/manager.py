from __future__ import annotations

import asyncio
from typing import Dict, Set

from .pipeline import SystemRegistries, execute_pipeline


class PipelineManager:
    """Manage concurrent pipeline executions."""

    def __init__(self, registries: SystemRegistries) -> None:
        self._registries = registries
        self._tasks: Set[asyncio.Task] = set()

    def start_pipeline(self, message: str) -> asyncio.Task:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        task = loop.create_task(self._run_pipeline(message))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def _run_pipeline(self, message: str) -> Dict:
        return await execute_pipeline(message, self._registries)

    async def run_pipeline(self, message: str) -> Dict:
        return await self._run_pipeline(message)

    def has_active_pipelines(self) -> bool:
        return any(not t.done() for t in self._tasks)
