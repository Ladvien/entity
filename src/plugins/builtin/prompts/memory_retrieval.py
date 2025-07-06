from __future__ import annotations

"""Retrieve past conversation from memory for further prompts."""


from typing import List

from pipeline.base_plugins import PromptPlugin
from pipeline.context import ConversationEntry, PluginContext
from pipeline.resources.memory_resource import MemoryResource


class MemoryRetrievalPrompt(PromptPlugin):
    """Fetch past conversation from memory and append it to the context."""

    dependencies = ["memory", "llm"]

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
