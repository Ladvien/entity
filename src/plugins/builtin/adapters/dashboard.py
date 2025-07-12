from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import InputAdapterPlugin
from entity.pipeline.stages import PipelineStage


class DashboardAdapter(InputAdapterPlugin):
    """Placeholder dashboard adapter."""

    stages = [PipelineStage.INPUT, PipelineStage.OUTPUT]

    def __init__(self, manager: Any, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.manager = manager
        self.app = object()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def serve(self, capabilities: Any) -> None:  # pragma: no cover - stub
        return None
