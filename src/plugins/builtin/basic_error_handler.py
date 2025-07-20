from __future__ import annotations

from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import FailurePlugin
from entity.pipeline.stages import PipelineStage


class BasicErrorHandler(FailurePlugin):
    """Log failure details and generate a fallback message."""

    name = "basic_error_handler"
    dependencies = ["logging"]
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> Any:
        logger = context.get_resource("logging")
        info = context.failure_info

        if info is None:
            if logger is not None:
                await logger.log(
                    "error",
                    "pipeline failure",
                    component="pipeline",
                    user_id=context.user_id,
                    pipeline_id=context.pipeline_id,
                    stage=str(context.current_stage),
                )
            message = {
                "error": "System error occurred",
                "message": "An unexpected error prevented processing your request.",
                "error_id": context.pipeline_id,
                "type": "static_fallback",
            }
        else:
            if logger is not None:
                await logger.log(
                    "error",
                    "plugin failure",
                    component="pipeline",
                    user_id=context.user_id,
                    pipeline_id=context.pipeline_id,
                    stage=info.stage,
                    plugin_name=info.plugin_name,
                    error_type=info.error_type,
                    error=info.error_message,
                )
            message = {
                "error": info.error_message,
                "message": "Unable to process request",
                "error_id": context.pipeline_id,
                "plugin": info.plugin_name,
                "stage": info.stage,
                "type": "plugin_error",
            }

        await context.think("failure_response", message)
