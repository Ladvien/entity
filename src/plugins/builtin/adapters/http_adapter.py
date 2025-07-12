from __future__ import annotations

from typing import Any, Dict

from entity.core.plugins import InputAdapterPlugin
from pipeline.stages import PipelineStage


class HTTPAdapter(InputAdapterPlugin):
    """Placeholder HTTP adapter."""

    stages = [PipelineStage.INPUT, PipelineStage.OUTPUT]

    def __init__(self, manager: Any, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.manager = manager
        self.app = object()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None
