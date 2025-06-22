# src/shared/utils.py - FIXED VERSION

from src.shared.models import ChatResponse
from src.shared.agent_result import AgentResult


def agent_result_to_response(result: AgentResult) -> ChatResponse:
    """Convert AgentResult to ChatResponse with proper serialization"""

    # ✅ Convert intermediate steps to serializable format
    serializable_steps = []
    if result.intermediate_steps:
        for step in result.intermediate_steps:
            if isinstance(step, (list, tuple)) and len(step) == 2:
                action, observation = step
                # Convert to dict format
                step_dict = {
                    "action": {
                        "tool": getattr(action, "tool", ""),
                        "tool_input": str(getattr(action, "tool_input", "")),
                        "log": getattr(action, "log", ""),
                    },
                    "observation": str(observation),
                }
                serializable_steps.append(step_dict)
            else:
                # Handle other formats
                serializable_steps.append({"raw": str(step)})

    # ✅ Convert react steps to serializable format
    serializable_react_steps = []
    if result.react_steps:
        for step in result.react_steps:
            serializable_react_steps.append(
                {
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": step.observation,
                    "final_answer": step.final_answer,
                }
            )

    return ChatResponse(
        thread_id=result.thread_id,
        timestamp=result.timestamp,
        raw_input=result.raw_input,
        raw_output=result.raw_output,
        response=result.final_response,
        tools_used=result.tools_used,
        token_count=result.token_count,
        memory_context=result.memory_context,
        intermediate_steps=serializable_steps,
        react_steps=serializable_react_steps,
    )
