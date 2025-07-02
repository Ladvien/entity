from __future__ import annotations

from typing import List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.plugins.resources.memory_resource import MemoryResource
from pipeline.stages import PipelineStage


class ComplexPrompt(PromptPlugin):
    """Generate responses using conversation history and memory search.

    Demonstrates **Plugin Composition (10)** by combining the LLM with the
    shared ``memory`` resource to craft a context-aware reply.
    """

    dependencies = ["llm", "memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        """Compose a context-aware reply.

        Steps:
        1. Load recent history from the database.
        2. Embed the latest user message and find similar entries.
        3. Call the LLM to create a reply.
        4. Record the reply in the conversation and set the pipeline response.
        """

        memory: MemoryResource = context.get_resource("memory")

        history: List[ConversationEntry] = []
        if memory:
            history = await memory.load_conversation(context.pipeline_id)
        history_text = "\n".join(f"{h.role}: {h.content}" for h in history)

        last_message = ""
        for entry in reversed(context.get_conversation_history()):
            if entry.role == "user":
                last_message = entry.content
                break

        similar: List[str] = []
        if memory:
            k = int(self.config.get("k", 3))
            similar = await memory.search_similar(last_message, k)
        similar_text = "; ".join(similar)

        prompt = (
            "Conversation history:\n"
            + history_text
            + "\nSimilar topics: "
            + similar_text
            + f"\nUser: {last_message}\nAssistant:"
        )

        response = await self.call_llm(context, prompt, purpose="complex_prompt")

        context.add_conversation_entry(
            content=response.content,
            role="assistant",
            metadata={"source": "complex_prompt"},
        )
        context.set_response(response.content)
        if memory:
            await memory.save_conversation(
                context.pipeline_id, context.get_conversation_history()
            )
