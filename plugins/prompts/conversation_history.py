from plugins.prompts.conversation_history import ConversationHistory

<<<<<<< HEAD:src/pipeline/plugins/prompts/conversation_history.py
__all__ = ["ConversationHistory"]
=======
from typing import Dict, List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage
from plugins.resources.memory_resource import MemoryResource


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
>>>>>>> 64d27a1aceba096733b70814249d0a84f4b3bce4:plugins/prompts/conversation_history.py
