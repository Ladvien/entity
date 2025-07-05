from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Any, Dict, cast

from registry import SystemRegistries

from .manager import PipelineManager


@dataclass
class AgentRuntime:
    """Execute messages through the pipeline."""

    registries: SystemRegistries

    def __post_init__(self) -> None:
        self.manager: PipelineManager[Any] = PipelineManager(self.registries)

    async def run_pipeline(self, message: str) -> Dict[str, Any]:
        async with self.registries.resources:
            result = await self.manager.run_pipeline(message)
            return cast(Dict[str, Any], result)

    async def handle(self, message: str) -> Dict[str, Any]:
        """Alias for :meth:`run_pipeline`."""

        return await self.run_pipeline(message)

    async def __aenter__(self) -> "AgentRuntime":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if hasattr(self.registries.resources, "shutdown_all"):
            await self.registries.resources.shutdown_all()
