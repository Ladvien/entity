from __future__ import annotations

from typing import List

from ...core.context import ConversationEntry, PluginContext
from ...core.plugins import PromptPlugin
from ...core.stages import PipelineStage


class PlanAndExecutePrompt(PromptPlugin):
    """Plan tasks for a goal and mark them completed."""

    dependencies = ["llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        goal = self._latest_user_message(context.conversation())
        planning_prompt = f"Break the goal into steps: {goal}"
        plan = await self.call_llm(context, planning_prompt, purpose="plan")
        steps = self._parse_steps(plan.content)
        await context.think("plan", steps)

        results: List[str] = []
        for index, step in enumerate(steps, 1):
            exec_prompt = f"Execute step {index}: {step}"
            result = await self.call_llm(
                context, exec_prompt, purpose=f"execute_{index}"
            )
            results.append(result.content)
            await context.think(f"step_{index}", result.content)

        await context.think("results", results)
        await context.think("completed", True)

    def _latest_user_message(self, conversation: List[ConversationEntry]) -> str:
        user_entries = [e.content for e in conversation if e.role == "user"]
        return user_entries[-1] if user_entries else ""

    def _parse_steps(self, text: str) -> List[str]:
        steps = [line.strip(" .") for line in text.splitlines() if line.strip()]
        return steps
