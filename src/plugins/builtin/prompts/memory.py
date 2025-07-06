from __future__ import annotations

"""Store conversation messages in the configured memory resource."""


from typing import Dict

from pipeline.base_plugins import PromptPlugin
from pipeline.context import PluginContext
from pipeline.resources.memory_resource import MemoryResource
from pipeline.stages import PipelineStage


class MemoryPlugin(PromptPlugin):
    """Persist conversation history using the ``memory`` resource."""

    dependencies = ["memory"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: MemoryResource = context.get_resource("memory")
        if memory is None:
            return

        if context.current_stage == PipelineStage.PARSE:
            history = await memory.load_conversation(context.pipeline_id)
            for entry in history:
                context.add_conversation_entry(
                    content=entry.content,
                    role=entry.role,
                    metadata=entry.metadata,
                )
        else:
            await memory.save_conversation(
                context.pipeline_id, context.get_conversation_history()
            )


__all__ = ["MemoryPlugin"]
