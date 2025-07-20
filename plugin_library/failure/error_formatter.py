from __future__ import annotations

from entity.plugins.base import FailurePlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from entity.core.context import PluginContext
from entity.core.stages import PipelineStage


class ErrorFormatter(FailurePlugin):
    """Generate a simple user message from captured failure information."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        failure_msg = await context.reflect("failure_response")
        if failure_msg is None:
            failure_msg = {
                "error": "System error occurred",
                "message": "An unexpected error prevented processing your request.",
                "error_id": context.pipeline_id,
                "type": "static_fallback",
            }
        elif hasattr(failure_msg, "to_dict"):
            failure_msg = failure_msg.to_dict()
        await context.think("failure_response", failure_msg)
