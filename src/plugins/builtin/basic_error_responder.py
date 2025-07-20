from __future__ import annotations

from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.pipeline.stages import PipelineStage


class BasicErrorResponder(PromptPlugin):
    """Emit a formatted message for recorded failures."""

    name = "basic_error_responder"
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> Any:
        info = context.failure_info
        if info is None:
            message = {
                "error": "System error occurred",
                "message": "An unexpected error prevented processing your request.",
                "error_id": context.pipeline_id,
                "type": "static_fallback",
            }
        else:
            message = {
                "error": info.error_message,
                "message": "Unable to process request",
                "error_id": context.pipeline_id,
                "plugin": info.plugin_name,
                "stage": info.stage,
                "type": "plugin_error",
            }
        await context.say(message)
