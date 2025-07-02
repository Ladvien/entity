from __future__ import annotations

from typing import List

from pipeline.context import PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ComplexPrompt(PromptPlugin):
    """Generate responses using vector memory."""

    dependencies = ["llm", "vector_memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        """Compose a context-aware reply."""
        vector_memory = context.get_resource("vector_memory")

        history_text = "\n".join(
            f"{h.role}: {h.content}" for h in context.get_conversation_history()
        )

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
