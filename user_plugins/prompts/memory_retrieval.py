from __future__ import annotations

from typing import List

from pipeline.base_plugins import PromptPlugin
from pipeline.context import ConversationEntry, PluginContext
from pipeline.resources.memory import Memory
from pipeline.stages import PipelineStage


class MemoryRetrievalPrompt(PromptPlugin):
    """Fetch past conversation from memory and append it to the context."""

    dependencies = ["memory", "llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: Memory = context.get_resource("memory")
        history: List[ConversationEntry] = await memory.load_conversation(
            context.pipeline_id
        )
        for entry in history:
            context.add_conversation_entry(
                content=entry.content,
                role=entry.role,
                metadata=entry.metadata,
            )
