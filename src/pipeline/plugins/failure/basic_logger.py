from __future__ import annotations

import logging
from typing import Any

from pipeline.context import PluginContext
from pipeline.plugins import FailurePlugin
from pipeline.stages import PipelineStage


class BasicLogger(FailurePlugin):
    """Log failure information using Python's logging module.

    Implements **Error Communication (30)** so users receive clear
    messages when something goes wrong.
    """

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> Any:
<<<<<< codex/add-docstring-to-baseplugin-class
        info = context.get_failure_info()
        logger = logging.getLogger(self.__class__.__name__)
        try:
======
        logger = logging.getLogger(self.__class__.__name__)
        try:
            info = context.get_failure_info()
>>>>>> main
            if info is not None:
                logger.error(
                    "Pipeline failure encountered",
                    extra={
                        "stage": info.stage,
                        "plugin": info.plugin_name,
                        "error": info.error_message,
                    },
                )
            else:
                logger.error("Pipeline failure encountered with no context")
        except Exception as exc:  # pragma: no cover - logging must not fail
            logging.getLogger(__name__).exception(
                "BasicLogger failed while handling an error: %s", exc
            )
