"""Template for prompt plugin."""

from pipeline.base_plugins import PromptPlugin
from pipeline.stages import PipelineStage


class {class_name}(PromptPlugin):
    """Example prompt plugin."""

    stages = [PipelineStage.THINK]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        if context.has("answer"):
            context.say(context.load("answer"))
            return

        result = await context.tool_use("some_tool", query=context.message)
        context.store("answer", result)
        context.say(result)
