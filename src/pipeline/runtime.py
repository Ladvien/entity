from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, cast

from registry import SystemRegistries

from .manager import PipelineManager, ResultT


@dataclass
class AgentRuntime(Generic[ResultT]):
    """Execute messages through the pipeline."""

    registries: SystemRegistries

    def __post_init__(self) -> None:
        self.manager = PipelineManager[ResultT](self.registries)

    async def run_pipeline(self, message: str) -> ResultT:
        return await self.manager.run_pipeline(message)

    async def handle(self, message: str) -> ResultT:
        """Alias for :meth:`run_pipeline`."""

        return await self.run_pipeline(message)
