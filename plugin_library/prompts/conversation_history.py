from __future__ import annotations

from typing import List

from entity.plugins.base import PromptPlugin
from entity.core.state import ConversationEntry
from entity.core.context import PluginContext
from entity.resources.memory import Memory
from entity.core.stages import PipelineStage


class ConversationHistory(PromptPlugin):
    """Load previous conversation from ``Memory`` into the current context."""

    dependencies = ["memory"]
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: Memory | None = context.get_memory()
        if memory is None:
            return

        history: List[ConversationEntry] = await memory.load_conversation(
            context.pipeline_id, user_id=context.user_id
        )
        context._state.conversation = history
