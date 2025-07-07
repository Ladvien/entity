from __future__ import annotations

"""Adapter that writes pipeline responses to the log."""

import logging
from typing import Any

from pipeline.base_plugins import AdapterPlugin
from pipeline.stages import PipelineStage


class LoggingAdapter(AdapterPlugin):
    """Log the final pipeline response during the deliver stage."""

    stages = [PipelineStage.DELIVER]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.logger = logging.getLogger("pipeline.output")
        if self.logger.getEffectiveLevel() > logging.INFO:
            self.logger.setLevel(logging.INFO)

    async def serve(self, registries) -> None:  # pragma: no cover - no server
        pass

    async def _execute_impl(self, context) -> None:
        """Log the pipeline response if one has been produced."""
        response = context.response
        if response is not None:
            self.logger.info("response delivered", extra={"response": response})
