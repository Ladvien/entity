from __future__ import annotations

import logging
from typing import Any

from pipeline.base_plugins import FailurePlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from pipeline.context import PluginContext
from pipeline.stages import PipelineStage


class BasicLogger(FailurePlugin):
    """Log failure information using Python's logging module."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> Any:
        logger = logging.getLogger(self.__class__.__name__)
        try:
            info = context.get_failure_info()
            if info is not None:
                snapshot = info.context_snapshot
                logger.error(
                    "Pipeline failure encountered",
                    extra={
                        "stage": info.stage,
                        "plugin": info.plugin_name,
                        "error": info.error_message,
                        "type": info.error_type,
                        "pipeline_id": context.request_id,
                        "retry_count": context.state.iteration,
                        **({"context_snapshot": snapshot} if snapshot else {}),
                    },
                )
            else:
                logger.error(
                    "Pipeline failure encountered with no context",
                    extra={
                        "pipeline_id": context.request_id,
                        "stage": str(context.current_stage),
                    },
                )
        except Exception as exc:  # pragma: no cover - logging must not fail
            logging.getLogger(__name__).exception(
                "BasicLogger failed while handling an error: %s", exc
            )
