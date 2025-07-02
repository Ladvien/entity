from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ReActPrompt(PromptPlugin):
    """Reasoning and acting in a loop using an LLM.

    Combines tool use and reflection to illustrate **Structured LLM Access (22)**
    and **Plugin-Level Iteration (26)** in tandem.
    """

    dependencies = ["llm"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        max_steps = int(self.config.get("max_steps", 5))

        conversation = context.get_conversation_history()
        user_messages = [e.content for e in conversation if e.role == "user"]
        question = user_messages[-1] if user_messages else "No question provided"

        for step in range(max_steps):
            step_context = self._build_step_context(
                context.get_conversation_history(), question
            )

            thought_prompt = (
                "Think step by step about this problem:\n\n"
                f"Context: {step_context}\n\n"
                "What should I think about next?"
            )
            thought = await self.call_llm(
                context, thought_prompt, purpose=f"react_thought_step_{step}"
            )

            context.add_conversation_entry(
                content=f"Thought: {thought.content}",
                role="assistant",
                metadata={"react_step": step, "type": "thought"},
            )

            action_prompt = (
                f'Based on my thought: "{thought.content}"\n'
                "Should I:\n1. Take an action (specify: search, calculate, etc.)\n"
                "2. Give a final answer\n\n"
                'Respond with either "Action: <action_name> <parameters>" '
                'or "Final Answer: <answer>"'
            )
            action_decision = await self.call_llm(
                context, action_prompt, purpose=f"react_action_step_{step}"
            )

            if action_decision.content.startswith("Final Answer:"):
                final_answer = action_decision.content.replace(
                    "Final Answer:", ""
                ).strip()
                context.set_response(final_answer)
                return
            if action_decision.content.startswith("Action:"):
                action_text = action_decision.content.replace("Action:", "").strip()
                action_name, params = self._parse_action(action_text)

                context.add_conversation_entry(
                    content=f"Action: {action_text}",
                    role="assistant",
                    metadata={"react_step": step, "type": "action"},
                )

                context.execute_tool(action_name, params)

        context.set_response(
            "I've reached my reasoning limit without finding a definitive answer."
        )

    def _build_step_context(
        self, conversation: List[ConversationEntry], question: str
    ) -> str:
        """Return a summary of ``conversation`` for the next reasoning step."""
        context_parts = [f"Question: {question}"]

        recent_entries = conversation[-10:]
        for entry in recent_entries:
            if entry.role == "assistant" and entry.metadata.get("type") in [
                "thought",
                "action",
            ]:
                context_parts.append(f"{entry.content}")
            elif entry.role == "system" and "Tool result:" in entry.content:
                context_parts.append(
                    f"Observation: {entry.content.replace('Tool result: ', '')}"
                )

        return "\n".join(context_parts)

    def _parse_action(self, action_text: str) -> Tuple[str, Dict[str, Any]]:
        """Parse an action command from ``action_text``."""
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
