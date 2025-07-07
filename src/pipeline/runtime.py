from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from registry import SystemRegistries

from .manager import PipelineManager


@dataclass
class AgentRuntime:
    """Execute messages through the pipeline."""

    registries: SystemRegistries
    manager: PipelineManager[Dict[str, Any]]

    def __post_init__(self) -> None:
        self.manager = PipelineManager[Dict[str, Any]](self.registries)

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
        tb: Any,
    ) -> None:
        if hasattr(self.registries.resources, "shutdown_all"):
            await self.registries.resources.shutdown_all()
