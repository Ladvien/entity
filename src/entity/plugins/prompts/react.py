from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..core.context import ConversationEntry, PluginContext
from ..core.plugins import PromptPlugin
from ..core.stages import PipelineStage


class ReActPrompt(PromptPlugin):
    """Reason and act iteratively using the ReAct pattern."""

    dependencies = ["llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        max_steps = int(self.config.get("max_steps", 5))
        conversation = context.conversation()
        user_messages = [e.content for e in conversation if e.role == "user"]
        question = user_messages[-1] if user_messages else "No question provided"

        steps: List[Dict[str, str]] = []

        for step in range(max_steps):
            step_context = self._build_step_context(context.conversation(), question)
            thought_prompt = (
                "Think step by step about this problem:\n\n"
                f"Context: {step_context}\n\n"
                "What should I think about next?"
            )
            thought = await self.call_llm(
                context, thought_prompt, purpose=f"react_thought_step_{step}"
            )
            context.think(f"thought_{step}", thought.content)
            step_record: Dict[str, str] = {"thought": thought.content}

            action_prompt = (
                f'Based on my thought: "{thought.content}"\n'
                "Should I:\n1. Take an action (specify: search, calculate, etc.)\n"
                "2. Give a final answer\n\n"
                'Respond with either "Action: <action_name> <parameters>" '
                'or "Final Answer: <answer>"'
            )
            decision = await self.call_llm(
                context, action_prompt, purpose=f"react_action_step_{step}"
            )

            if decision.content.startswith("Final Answer:"):
                answer = decision.content.replace("Final Answer:", "").strip()
                context.think("final_answer", answer)
                steps.append(step_record)
                context.store("react_steps", steps)
                return

            if decision.content.startswith("Action:"):
                action_text = decision.content.replace("Action:", "").strip()
                action_name, params = self._parse_action(action_text)
                step_record["action"] = action_text
                context.think(f"action_{step}", action_text)
                await context.tool_use(action_name, **params)

            steps.append(step_record)

        context.think(
            "final_answer",
            "I've reached my reasoning limit without finding a definitive answer.",
        )
        context.store("react_steps", steps)

    def _build_step_context(
        self, conversation: List[ConversationEntry], question: str
    ) -> str:
        parts = [f"Question: {question}"]
        recent_entries = conversation[-10:]
        for entry in recent_entries:
            if entry.role == "assistant" and entry.metadata.get("type") in [
                "thought",
                "action",
            ]:
                parts.append(entry.content)
            elif entry.role == "system" and "Tool result:" in entry.content:
                parts.append(
                    f"Observation: {entry.content.replace('Tool result: ', '')}"
                )
        return "\n".join(parts)

    def _parse_action(self, action_text: str) -> Tuple[str, Dict[str, Any]]:
        parts = action_text.split(" ", 1)
        if len(parts) < 2:
            return "search_tool", {"query": action_text}

        action_name = parts[0].lower()
        params_text = parts[1]

        if action_name == "search":
            return "search_tool", {"query": params_text}
        if action_name == "calculate":
            return "calculator_tool", {"expression": params_text}
        return "search_tool", {"query": action_text}
