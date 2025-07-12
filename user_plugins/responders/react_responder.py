from __future__ import annotations

from typing import List

from entity.core.context import PluginContext
from entity.core.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ReactResponder(PromptPlugin):
    """Provide the final answer from ``ReActPrompt`` reasoning."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        thoughts: List[str] = await context.reflect("react_thoughts", [])
        actions: List[str] = await context.reflect("react_actions", [])
        final_answer = await context.reflect("react_final_answer", "")
        if final_answer:
            await context.say(final_answer)
            return
        parts: list[str] = []
        for t in thoughts:
            parts.append(f"Thought: {t}")
        for a in actions:
            parts.append(f"Action: {a}")
        await context.say("\n".join(parts))
