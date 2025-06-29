from __future__ import annotations

import logging
from typing import Any

from pipeline.context import PluginContext
from pipeline.plugins import FailurePlugin
from pipeline.stages import PipelineStage


class BasicLogger(FailurePlugin):
    """Log failure information using Python's logging module."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> Any:
        info = context._state.failure_info
        logger = logging.getLogger(self.__class__.__name__)
        logger.error(
            "Pipeline failure encountered",
            extra={
                "stage": info.stage,
                "plugin": info.plugin_name,
                "error": info.error_message,
            },
        )
