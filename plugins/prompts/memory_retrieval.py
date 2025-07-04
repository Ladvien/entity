from plugins.prompts.memory_retrieval import MemoryRetrievalPrompt

<<<<<<< HEAD:src/pipeline/plugins/prompts/memory_retrieval.py
__all__ = ["MemoryRetrievalPrompt"]
=======
from typing import List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage
from plugins.resources.memory_resource import MemoryResource


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
>>>>>>> 64d27a1aceba096733b70814249d0a84f4b3bce4:plugins/prompts/memory_retrieval.py
