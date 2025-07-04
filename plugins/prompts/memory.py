from plugins.prompts.memory import MemoryPlugin

<<<<<<< HEAD:src/pipeline/plugins/prompts/memory.py
__all__ = ["MemoryPlugin"]
=======
from typing import Dict

from pipeline.context import PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage
from plugins.resources.memory_resource import MemoryResource


class MemoryPlugin(PromptPlugin):
    """Persist conversation history using the ``memory`` resource."""

    dependencies = ["memory"]
    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

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
>>>>>>> 64d27a1aceba096733b70814249d0a84f4b3bce4:plugins/prompts/memory.py
