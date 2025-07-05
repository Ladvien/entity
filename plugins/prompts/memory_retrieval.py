from __future__ import annotations

"""Retrieve past conversation from memory for further prompts."""


from typing import List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.resources.memory_resource import MemoryResource
from pipeline.stages import PipelineStage
from pipeline.user_plugins import PromptPlugin


class MemoryRetrievalPrompt(PromptPlugin):
    """Fetch past conversation from memory and append it to the context."""

    dependencies = ["memory", "llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: MemoryResource = context.get_resource("memory")
        history: List[ConversationEntry] = await memory.load_conversation(
            context.pipeline_id
        )
        for entry in history:
            context.add_conversation_entry(
                content=entry.content,
                role=entry.role,
                metadata=entry.metadata,
            )


__all__ = ["MemoryRetrievalPrompt"]
