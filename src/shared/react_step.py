from dataclasses import dataclass
from rich.text import Text
from typing import List, Dict, Any


@dataclass
class ReActStep:
    thought: str
    action: str
    action_input: str
    observation: str
    final_answer: str

    def format_rich(self) -> Text:
        text = Text()
        text.append("Thought: ", style="cyan").append(f"{self.thought}\n")
        text.append("Action: ", style="blue").append(f"{self.action}\n")
        text.append("Action Input: ", style="magenta").append(f"{self.action_input}\n")
        text.append("Observation: ", style="yellow").append(f"{self.observation}\n")
        if self.final_answer:
            text.append("Final Answer: ", style="green").append(f"{self.final_answer}")
        return text

    @staticmethod
    def extract_react_steps(intermediate_steps: List[Any]) -> List["ReActStep"]:
        steps = []

        for step in intermediate_steps:
            if isinstance(step, (list, tuple)) and len(step) == 2:
                action, observation = step

                steps.append(
                    ReActStep(
                        thought=getattr(action, "log", ""),
                        action=getattr(action, "tool", ""),
                        action_input=str(getattr(action, "tool_input", "")),
                        observation=str(observation),
                        final_answer="",  # filled in below if applicable
                    )
                )

        # Capture a final answer from the last step’s log if available
        if steps and "Final Answer:" in steps[-1].thought:
            match = steps[-1].thought.split("Final Answer:")[-1].strip()
            steps[-1].final_answer = match

        return steps
