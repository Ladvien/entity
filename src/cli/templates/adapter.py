"""Template for adapter plugin."""

from entity.core.plugins import AdapterPlugin
from entity.core.stages import PipelineStage


class {class_name}(AdapterPlugin):
    """Example adapter plugin."""

    stages = [PipelineStage.DELIVER]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        if context.has("response"):
            await context.queue_tool_use("send", {"text": context.load("response")})
