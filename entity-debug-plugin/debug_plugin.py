from __future__ import annotations

from pipeline.base_plugins import PromptPlugin
from pipeline.context import PluginContext
from pipeline.stages import PipelineStage


class DebugPrompt(PromptPlugin):
    """Simple prompt plugin for debugging."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        self.logger.info("DebugPrompt executed")
        context.add_conversation_entry(
            content="DebugPrompt executed",
            role="assistant",
        )
