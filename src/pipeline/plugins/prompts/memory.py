from __future__ import annotations

from typing import Dict

from pipeline.context import PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.resources.storage import StorageBackend
from pipeline.stages import PipelineStage


class MemoryPlugin(PromptPlugin):
    """Persist conversation history using a ``StorageBackend`` resource."""

    dependencies = ["storage"]
    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)

    async def _execute_impl(self, context: PluginContext) -> None:
        storage: StorageBackend = context.get_resource("storage")
        if storage is None:
            return

        if context.current_stage == PipelineStage.PARSE:
            history = await storage.load_history(context.pipeline_id)
            for entry in history:
                context.add_conversation_entry(
                    content=entry.content,
                    role=entry.role,
                    metadata=entry.metadata,
                )
        else:
            await storage.save_history(
                context.pipeline_id, context.get_conversation_history()
            )
