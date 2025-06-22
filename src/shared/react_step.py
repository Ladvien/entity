# Updated src/shared/react_step.py with better extraction

from dataclasses import dataclass
from rich.text import Text
from rich.console import Console
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReActStep:
    thought: str
    action: str
    action_input: str
    observation: str
    final_answer: str = ""

    def format_rich(self) -> Text:
        """Format this step for rich console output"""
        text = Text()

        if self.thought:
            text.append("🤔 Thought: ", style="cyan bold")
            text.append(f"{self.thought}\n", style="cyan")

        if self.action:
            text.append("⚙️ Action: ", style="yellow bold")
            text.append(f"{self.action}\n", style="yellow")

        if self.action_input:
            text.append("📝 Action Input: ", style="magenta bold")
            text.append(f"{self.action_input}\n", style="magenta")

        if self.observation:
            text.append("👁️ Observation: ", style="green bold")
            text.append(f"{self.observation}\n", style="green")

        if self.final_answer:
            text.append("✅ Final Answer: ", style="bright_green bold")
            text.append(f"{self.final_answer}", style="bright_green")

        return text

    def print_to_console(self, console: Console):
        """Print this step directly to console"""
        console.print(self.format_rich())

    @staticmethod
    def extract_react_steps(intermediate_steps: List[Any]) -> List["ReActStep"]:
        """Extract ReAct steps from LangChain intermediate steps"""
        steps = []

        logger.debug(f"🔍 Extracting from {len(intermediate_steps)} intermediate steps")

        for i, step in enumerate(intermediate_steps):
            logger.debug(f"🔍 Step {i}: {type(step)} - {step}")

            if isinstance(step, (list, tuple)) and len(step) == 2:
                action, observation = step

                # Extract data from action object
                thought = ""
                action_name = ""
                action_input = ""

                # Log what we found in the action object
                logger.debug(f"🔍 Action type: {type(action)}")
                logger.debug(f"🔍 Action attributes: {dir(action)}")

                if hasattr(action, "log"):
                    log = action.log
                    logger.debug(f"🔍 Action log: {log[:200]}...")

                    # Parse the thought from the log using more flexible regex
                    thought_patterns = [
                        r"Thought:\s*(.*?)(?=\nAction:|$)",
                        r"I need to (.*?)(?=\nAction:|$)",
                        r"I should (.*?)(?=\nAction:|$)",
                        r"^(.*?)(?=\nAction:|$)",  # Everything before Action
                    ]

                    for pattern in thought_patterns:
                        thought_match = re.search(
                            pattern, log, re.DOTALL | re.IGNORECASE
                        )
                        if thought_match:
                            thought = thought_match.group(1).strip()
                            break

                    # Parse action name
                    action_patterns = [
                        r"Action:\s*(.*?)(?=\nAction Input:|$)",
                        r"Action:\s*(\w+)",
                    ]

                    for pattern in action_patterns:
                        action_match = re.search(
                            pattern, log, re.DOTALL | re.IGNORECASE
                        )
                        if action_match:
                            action_name = action_match.group(1).strip()
                            break

                    # Parse action input
                    input_patterns = [
                        r"Action Input:\s*(.*?)(?=\nObservation:|$)",
                        r"Action Input:\s*(.*)",
                    ]

                    for pattern in input_patterns:
                        input_match = re.search(pattern, log, re.DOTALL | re.IGNORECASE)
                        if input_match:
                            action_input = input_match.group(1).strip()
                            break

                # Fallback to direct attributes
                if not action_name and hasattr(action, "tool"):
                    action_name = action.tool

                if not action_input and hasattr(action, "tool_input"):
                    action_input = str(action.tool_input)

                # Create the step
                react_step = ReActStep(
                    thought=thought,
                    action=action_name,
                    action_input=action_input,
                    observation=str(observation),
                    final_answer="",
                )

                logger.debug(
                    f"✅ Created step: thought='{thought[:50]}...', action='{action_name}', input='{action_input[:50]}...', obs='{str(observation)[:50]}...'"
                )
                steps.append(react_step)

        # Extract final answer from the last step's thought if available
        if steps:
            last_step = steps[-1]
            if "Final Answer:" in last_step.thought:
                final_answer_match = re.search(
                    r"Final Answer:\s*(.*)", last_step.thought, re.DOTALL
                )
                if final_answer_match:
                    last_step.final_answer = final_answer_match.group(1).strip()

        logger.info(f"✅ Extracted {len(steps)} ReAct steps from intermediate steps")
        return steps

    @staticmethod
    def extract_from_raw_output(raw_output: str) -> List["ReActStep"]:
        """Extract ReAct steps from raw LLM output text"""
        logger.debug(f"🔍 Extracting from raw output: {raw_output[:200]}...")
        steps = []

        # Try to find clear ReAct pattern in the output
        if "Thought:" in raw_output and "Action:" in raw_output:
            # Split on pattern boundaries
            sections = re.split(r"(?=Thought:)", raw_output)

            for section in sections:
                if not section.strip():
                    continue

                # Extract components using regex
                thought_match = re.search(
                    r"Thought:\s*(.*?)(?=\nAction:|$)", section, re.DOTALL
                )
                action_match = re.search(
                    r"Action:\s*(.*?)(?=\nAction Input:|$)", section, re.DOTALL
                )
                input_match = re.search(
                    r"Action Input:\s*(.*?)(?=\nObservation:|$)", section, re.DOTALL
                )
                observation_match = re.search(
                    r"Observation:\s*(.*?)(?=\nThought:|$)", section, re.DOTALL
                )
                final_match = re.search(r"Final Answer:\s*(.*)", section, re.DOTALL)

                # Only create step if we have meaningful content
                if thought_match or action_match:
                    step = ReActStep(
                        thought=thought_match.group(1).strip() if thought_match else "",
                        action=action_match.group(1).strip() if action_match else "",
                        action_input=(
                            input_match.group(1).strip() if input_match else ""
                        ),
                        observation=(
                            observation_match.group(1).strip()
                            if observation_match
                            else ""
                        ),
                        final_answer=(
                            final_match.group(1).strip() if final_match else ""
                        ),
                    )
                    steps.append(step)

        # If no clear ReAct pattern, create a single step with the whole output
        if not steps and raw_output.strip():
            logger.debug("🔍 No clear ReAct pattern found, creating single step")
            steps = [
                ReActStep(
                    thought="",
                    action="",
                    action_input="",
                    observation="",
                    final_answer=raw_output.strip(),
                )
            ]

        logger.info(f"✅ Extracted {len(steps)} ReAct steps from raw output")
        return steps
