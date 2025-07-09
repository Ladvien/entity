from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import AdapterPlugin
from pipeline.stages import PipelineStage


class CLIAdapter(AdapterPlugin):
    """Placeholder CLI adapter."""

    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

    def __init__(self, manager: Any, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.manager = manager

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def serve(self, capabilities: Any) -> None:  # pragma: no cover - stub
        return None
