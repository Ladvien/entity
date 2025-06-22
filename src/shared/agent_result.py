# Update src/shared/agent_result.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.shared.react_step import ReActStep


@dataclass
class AgentResult:
    thread_id: str
    timestamp: datetime
    raw_input: str
    raw_output: str
    final_response: str
    tools_used: List[str]
    token_count: int
    memory_context: str
    intermediate_steps: List[Any]  # Keep original format for internal use
    react_steps: Optional[List[ReActStep]] = None

    def to_serializable_dict(self) -> Dict[str, Any]:
        """Convert to a fully serializable dictionary for API responses"""

        # Convert intermediate steps to serializable format
        serializable_steps = []
        if self.intermediate_steps:
            for step in self.intermediate_steps:
                if isinstance(step, (list, tuple)) and len(step) == 2:
                    action, observation = step
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
                    serializable_steps.append({"raw": str(step)})

        # Convert react steps to serializable format
        serializable_react_steps = []
        if self.react_steps:
            for step in self.react_steps:
                serializable_react_steps.append(
                    {
                        "thought": step.thought,
                        "action": step.action,
                        "action_input": step.action_input,
                        "observation": step.observation,
                        "final_answer": step.final_answer,
                    }
                )

        return {
            "thread_id": self.thread_id,
            "timestamp": self.timestamp.isoformat(),
            "raw_input": self.raw_input,
            "raw_output": self.raw_output,
            "final_response": self.final_response,
            "tools_used": self.tools_used,
            "token_count": self.token_count,
            "memory_context": self.memory_context,
            "intermediate_steps": serializable_steps,
            "react_steps": serializable_react_steps,
        }
