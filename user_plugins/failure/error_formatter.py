from __future__ import annotations

from pipeline.base_plugins import FailurePlugin
from pipeline.context import PluginContext
from pipeline.errors import ErrorResponse
from pipeline.stages import PipelineStage


class ErrorFormatter(FailurePlugin):
    """Generate a simple user message from captured failure information."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        info = context.get_failure_info()
        if info is None:
            context.set_response(ErrorResponse({"error": "Unknown error"}).to_dict())
            return
        message = f"{info.plugin_name} failed ({info.error_type}): {info.error_message}"
        context.set_response(ErrorResponse({"error": message}).to_dict())
