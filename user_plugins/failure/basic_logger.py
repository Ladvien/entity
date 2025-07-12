from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from entity.core.plugins import FailurePlugin

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from entity.core.context import PluginContext

from entity.core.stages import PipelineStage


class BasicLogger(FailurePlugin):
    """Log failure information using Python's logging module."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> Any:
        logger = logging.getLogger(self.__class__.__name__)
        try:
            info = context.failure_info
            if info is not None:
                logger.error(
                    "Pipeline failure encountered",
                    extra={
                        "stage": info.stage,
                        "plugin": info.plugin_name,
                        "error": info.error_message,
                        "type": info.error_type,
                        "pipeline_id": context.request_id,
                        "retry_count": getattr(
                            getattr(context, "_state", None), "iteration", 0
                        ),
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
