from __future__ import annotations

from typing import Any

from ...core.context import PluginContext
from ...core.plugins import FailurePlugin
from ...core.stages import PipelineStage


class BasicErrorHandler(FailurePlugin):
    """Log failure information and generate a fallback message."""

    dependencies = ["logging"]
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> Any:
        logging_res = context.get_resource("logging")
        info = context.failure_info
        if info is None:
            if logging_res is not None:
                await logging_res.log(
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
            if logging_res is not None:
                await logging_res.log(
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
        context._state.response = message
