from __future__ import annotations

from typing import List

from entity.core.plugins import PromptPlugin
from pipeline.context import ConversationEntry, PluginContext
from pipeline.stages import PipelineStage


class ChainOfThoughtPrompt(PromptPlugin):
    """Incremental reasoning via chain-of-thought.

    Exemplifies **Plugin-Level Iteration (26)** by looping over reasoning steps
    within a single plugin execution.
    """

    dependencies = ["llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        conversation_text = self._get_conversation_text(context.conversation())

        breakdown_prompt = f"Break this problem into logical steps: {conversation_text}"
        breakdown = await self.call_llm(
            context, breakdown_prompt, purpose="problem_breakdown"
        )
        context.say(
            f"Problem breakdown: {breakdown.content}",
            metadata={"reasoning_step": "breakdown"},
        )

        reasoning_steps: List[str] = []
        for step in range(self.config.get("max_steps", 5)):
            reasoning_prompt = (
                f"Reason through step {step + 1} of solving: {conversation_text}"
            )
            reasoning = await self.call_llm(
                context, reasoning_prompt, purpose=f"reasoning_step_{step + 1}"
            )
            reasoning_steps.append(reasoning.content)
            context.say(
                f"Reasoning step {step + 1}: {reasoning.content}",
                metadata={"reasoning_step": step + 1},
            )

            if self._needs_tools(reasoning.content):
                await context.tool_use(
                    "analysis_tool",
                    data=conversation_text,
                    reasoning_step=reasoning.content,
                )

            if "final answer" in reasoning.content.lower():
                break

        context.cache("reasoning_complete", True)
        context.cache("reasoning_steps", reasoning_steps)

    def _needs_tools(self, reasoning_text: str) -> bool:
        """Return True if ``reasoning_text`` suggests tool usage."""

        tool_indicators = ["need to calculate", "should look up", "requires analysis"]
        return any(indicator in reasoning_text.lower() for indicator in tool_indicators)

    def _get_conversation_text(self, conversation: List[ConversationEntry]) -> str:
        """Return the most recent user message from ``conversation``."""

        user_entries = [entry.content for entry in conversation if entry.role == "user"]
        return user_entries[-1] if user_entries else ""
