from __future__ import annotations

from typing import List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.plugins.resources.memory_resource import SimpleMemoryResource
from pipeline.stages import PipelineStage


class MemoryRetrievalPrompt(PromptPlugin):
    """Fetch past conversation from memory and append it to the context.

    Applies **Explicit Multi-Turn Support (27)** by retrieving prior messages
    when available.
    """

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: SimpleMemoryResource = context.get_resource("memory")
        history: List[ConversationEntry] = memory.get("history", [])
        if not history:
            db = context.get_resource("database")
            if db and hasattr(db, "load_history"):
                db_history = await db.load_history(context.pipeline_id)
                history.extend(db_history)
        for entry in history:
            context.add_conversation_entry(
                content=entry.content,
                role=entry.role,
                metadata=entry.metadata,
            )
