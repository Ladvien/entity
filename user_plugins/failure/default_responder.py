from __future__ import annotations

from entity.core.plugins import FailurePlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from entity.core.context import PluginContext
from entity.core.stages import PipelineStage


class DefaultResponder(FailurePlugin):
    """Return a standardized error message when failures occur."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        info = context.failure_info
        if info is None:
            await context.think(
                "failure_response",
                {
                    "error": "System error occurred",
                    "message": "An unexpected error prevented processing your request.",
                    "error_id": context.pipeline_id,
                    "type": "static_fallback",
                },
            )
        else:
            await context.think(
                "failure_response",
                {
                    "error": info.error_message,
                    "message": "Unable to process request",
                    "error_id": context.pipeline_id,
                    "plugin": info.plugin_name,
                    "stage": info.stage,
                    "type": "plugin_error",
                },
            )
