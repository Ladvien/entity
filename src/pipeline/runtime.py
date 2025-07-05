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

<<<<<<< HEAD
    async def run_pipeline(self, message: str) -> Dict[str, Any]:
        async with self.registries.resources:
            return await self.manager.run_pipeline(message)
=======
    async def run_pipeline(self, message: str) -> ResultT:
        return await self.manager.run_pipeline(message)
>>>>>>> 7f065b1474162305cfdc41a24e318e660ad8a8dd

    async def handle(self, message: str) -> ResultT:
        """Alias for :meth:`run_pipeline`."""

<<<<<<< HEAD
        return cast(Dict[str, Any], await self.run_pipeline(message))

    async def __aenter__(self) -> "AgentRuntime":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if hasattr(self.registries.resources, "shutdown_all"):
            await self.registries.resources.shutdown_all()
=======
        return await self.run_pipeline(message)
>>>>>>> 7f065b1474162305cfdc41a24e318e660ad8a8dd
