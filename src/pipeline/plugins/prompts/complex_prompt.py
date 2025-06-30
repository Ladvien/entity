from __future__ import annotations

from typing import List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ComplexPrompt(PromptPlugin):
    """Generate responses using DB history and vector memory."""

    dependencies = ["ollama", "database", "vector_memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        """Compose a context-aware reply.

        Steps:
        1. Load recent history from the database.
        2. Embed the latest user message and find similar entries.
        3. Call the LLM to create a reply.
        4. Record the reply in the conversation and set the pipeline response.
        """

        db = context.get_resource("database")
        vector_memory = context.get_resource("vector_memory")

        history: List[ConversationEntry] = []
        if db and hasattr(db, "load_history"):
            history = await db.load_history(context.pipeline_id)
        history_text = "\n".join(f"{h.role}: {h.content}" for h in history)

        last_message = ""
        for entry in reversed(context.get_conversation_history()):
            if entry.role == "user":
                last_message = entry.content
                break

        similar: List[str] = []
        if vector_memory:
            await vector_memory.add_embedding(last_message)
            k = int(self.config.get("k", 3))
            similar = await vector_memory.query_similar(last_message, k)
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
