from __future__ import annotations

from entity.core.context import PluginContext
from entity.core.plugins import PromptPlugin
from entity.pipeline.stages import PipelineStage


class ComplexPromptResponder(PromptPlugin):
    """Output the response built by ``ComplexPrompt``."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        reply = await context.reflect("complex_response", "")
        await context.say(reply)
