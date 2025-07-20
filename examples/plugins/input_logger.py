from __future__ import annotations

from entity.core.context import PluginContext
from entity.plugins.base import InputAdapterPlugin
from entity.core.stages import PipelineStage


class InputLogger(InputAdapterPlugin):
    """Record the raw user message."""

    stages = [PipelineStage.INPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        message = context.conversation()[-1].content if context.conversation() else ""
        await context.think("raw_input", message)
