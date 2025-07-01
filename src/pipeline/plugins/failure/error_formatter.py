from __future__ import annotations

from pipeline.context import PluginContext
from pipeline.plugins import FailurePlugin
from pipeline.stages import PipelineStage


class ErrorFormatter(FailurePlugin):
    """Generate a simple user message from captured failure information."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        info = context.get_failure_info()
        if info is None:
            context.set_response({"error": "Unknown error"})
            return
        message = f"{info.plugin_name} failed ({info.error_type}): {info.error_message}"
        context.set_response({"error": message})
