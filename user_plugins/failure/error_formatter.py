from __future__ import annotations

from entity.core.plugins import FailurePlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from entity.core.context import PluginContext
from pipeline.errors import create_static_error_response
from entity.pipeline.stages import PipelineStage


class ErrorFormatter(FailurePlugin):
    """Generate a simple user message from captured failure information."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        failure_msg = await context.reflect("failure_response")
        if failure_msg is None:
            failure_msg = create_static_error_response(context.pipeline_id).to_dict()
        elif hasattr(failure_msg, "to_dict"):
            failure_msg = failure_msg.to_dict()
        await context.say(failure_msg)
