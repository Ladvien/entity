from __future__ import annotations

from typing import List

from entity.core.plugins import PromptPlugin
from entity.core.context import PluginContext
from entity.core.stages import PipelineStage
from entity.resources.memory import Memory


class MemoryRetrievalPrompt(PromptPlugin):
    """Retrieve similar conversation snippets from ``Memory``."""

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: Memory | None = context.get_memory()
        if memory is None:
            return

        last_user = next(
            (
                entry.content
                for entry in reversed(context.conversation())
                if entry.role == "user"
            ),
            "",
        )

        k = int(self.config.get("k", 3))
        snippets: List[str] = await memory.search_similar(last_user, k)
        max_length = int(self.config.get("max_context_length", 4000))
        joined = "\n".join(snippets)[:max_length]
        await context.think("retrieved_memory", joined)
