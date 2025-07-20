from __future__ import annotations

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class MessageParser(PromptPlugin):
    """Normalize user input for later stages."""

    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context: PluginContext) -> None:
        raw = context.conversation()[-1].content if context.conversation() else ""
        await context.think("parsed_input", raw.strip().lower())
