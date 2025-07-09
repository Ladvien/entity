"""Template for adapter plugin."""

from pipeline.base_plugins import AdapterPlugin
from pipeline.stages import PipelineStage


class {class_name}(AdapterPlugin):
    """Example adapter plugin."""

    stages = [PipelineStage.DELIVER]
    # Execution order follows the YAML list or registration sequence; no priority field

    async def _execute_impl(self, context):
        if context.has("response"):
            await context.queue_tool_use("send", {"text": context.load("response")})
