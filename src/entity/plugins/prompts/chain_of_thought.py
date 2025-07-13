from __future__ import annotations

from typing import List

from ...core.context import ConversationEntry, PluginContext
from ...core.plugins import PromptPlugin
from ...core.stages import PipelineStage


class ChainOfThoughtPrompt(PromptPlugin):
    """Incrementally reason through a problem using an LLM."""

    dependencies = ["llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        conversation_text = self._latest_user_message(context.conversation())

        breakdown_prompt = f"Break this problem into logical steps: {conversation_text}"
        breakdown = await self.call_llm(
            context, breakdown_prompt, purpose="problem_breakdown"
        )
        context.think("problem_breakdown", breakdown.content)

        steps: List[str] = []
        for step in range(int(self.config.get("max_steps", 5))):
            reasoning_prompt = (
                f"Reason through step {step + 1} of solving: {conversation_text}"
            )
            reasoning = await self.call_llm(
                context, reasoning_prompt, purpose=f"reasoning_step_{step + 1}"
            )
            steps.append(reasoning.content)
            context.think(f"reasoning_step_{step + 1}", reasoning.content)

            if self._needs_tools(reasoning.content):
                await context.tool_use(
                    "analysis_tool",
                    data=conversation_text,
                    reasoning_step=reasoning.content,
                )

            if "final answer" in reasoning.content.lower():
                break

        await context.think("reasoning_complete", True)
        await context.think("reasoning_steps", steps)

    def _needs_tools(self, reasoning_text: str) -> bool:
        indicators = ["need to calculate", "should look up", "requires analysis"]
        return any(i in reasoning_text.lower() for i in indicators)

    def _latest_user_message(self, conversation: List[ConversationEntry]) -> str:
        user_entries = [e.content for e in conversation if e.role == "user"]
        return user_entries[-1] if user_entries else ""
