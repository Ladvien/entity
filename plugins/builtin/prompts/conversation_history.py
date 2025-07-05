from __future__ import annotations

"""Synchronize conversation history using the memory resource."""


from typing import Dict, List

from pipeline.base_plugins import PromptPlugin
from pipeline.context import ConversationEntry, PluginContext
from pipeline.resources.memory_resource import MemoryResource
from pipeline.stages import PipelineStage


class ConversationHistory(PromptPlugin):
    """Load and persist conversation history using the ``memory`` resource."""

    dependencies = ["memory"]
    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: MemoryResource = context.get_resource("memory")
        if memory is None:
            return
        if context.current_stage == PipelineStage.PARSE:
            rows = await memory.load_conversation(context.pipeline_id)
            for row in rows:
                context.add_conversation_entry(
                    content=row.content,
                    role=row.role,
                    metadata=row.metadata,
                    timestamp=row.timestamp,
                )
        else:
            history: List[ConversationEntry] = context.get_conversation_history()
            await memory.save_conversation(context.pipeline_id, history)


__all__ = ["ConversationHistory"]
