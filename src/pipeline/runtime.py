from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, cast

from registry import SystemRegistries

from .manager import PipelineManager


@dataclass
class AgentRuntime:
    """Execute messages through the pipeline."""

    registries: SystemRegistries

    def __post_init__(self) -> None:
        self.manager = PipelineManager(self.registries)

    async def run_pipeline(self, message: str) -> Dict[str, Any]:
        return await self.manager.run_pipeline(message)

    async def handle(self, message: str) -> Dict[str, Any]:
        """Alias for :meth:`run_pipeline`."""

        return cast(Dict[str, Any], await self.run_pipeline(message))
