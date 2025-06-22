# src/cli/render.py - Updated with clean final answer

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
import re

from src.shared.agent_result import AgentResult

console = Console()


def render_agent_result(result: AgentResult):
    """Render agent result with detailed ReAct steps"""

    # Show memory context if used
    if result.memory_context:
        console.print("[bold magenta]🧠 Using memory context...[/bold magenta]")
        console.print()

    # Show ReAct steps if available
    if result.react_steps and len(result.react_steps) > 0:
        console.print("[bold blue]🔄 Agent Reasoning Process:[/bold blue]")
        console.print()

        for i, step in enumerate(result.react_steps, 1):
            # Add a separator between steps (but not before the first)
            if i > 1:
                console.print(Rule(style="dim"))
                console.print()

            # Show step number
            console.print(f"[dim]Step {i}:[/dim]")

            # Create step display manually to handle any missing fields
            step_text = Text()

            if step.thought and step.thought.strip():
                step_text.append("🤔 Thought: ", style="cyan bold")
                step_text.append(f"{step.thought.strip()}\n", style="cyan")

            if step.action and step.action.strip():
                step_text.append("⚙️ Action: ", style="yellow bold")
                step_text.append(f"{step.action.strip()}\n", style="yellow")

            if step.action_input and step.action_input.strip():
                step_text.append("📝 Action Input: ", style="magenta bold")
                step_text.append(f"{step.action_input.strip()}\n", style="magenta")

            if step.observation and step.observation.strip():
                step_text.append("👁️ Observation: ", style="green bold")
                step_text.append(f"{step.observation.strip()}\n", style="green")

            # Only print if we have content
            if step_text.plain:
                console.print(step_text)
            else:
                console.print("[dim]Empty step[/dim]")

            console.print()

    # ✅ CLEAN the final response and show ONLY the actual answer in a box
    clean_final_response = _extract_clean_final_answer(result.final_response)

    console.print(
        Panel.fit(
            clean_final_response,
            title="💬 Final Answer",
            style="bold green",
            border_style="green",
        )
    )

    # Show metadata
    metadata_parts = []
    if result.tools_used:
        # Filter out _Exception from tools
        real_tools = [tool for tool in result.tools_used if tool != "_Exception"]
        if real_tools:
            metadata_parts.append(f"🛠️ Tools: {', '.join(real_tools)}")
    if result.memory_context:
        metadata_parts.append("🧠 Memory: Used")
    if result.token_count:
        metadata_parts.append(f"🔢 Tokens: {result.token_count}")

    if metadata_parts:
        console.print(f"[dim]   {' | '.join(metadata_parts)}[/dim]")


def _extract_clean_final_answer(raw_response: str) -> str:
    """Extract just the clean final answer, removing any extra reasoning"""

    # First, try to extract everything after "Final Answer:"
    final_answer_match = re.search(
        r"Final Answer:\s*(.*)", raw_response, re.DOTALL | re.IGNORECASE
    )
    if final_answer_match:
        answer = final_answer_match.group(1).strip()
    else:
        answer = raw_response.strip()

    # Remove any subsequent "Question:", "Thought:", "Action:" etc that leaked in
    cleanup_patterns = [
        r"\n\nQuestion:.*",  # Remove everything from "\n\nQuestion:" onwards
        r"\nQuestion:.*",  # Remove everything from "\nQuestion:" onwards
        r"\nThought:.*",  # Remove everything from "\nThought:" onwards
        r"\nAction:.*",  # Remove everything from "\nAction:" onwards
        r"\n\nThought:.*",  # Remove everything from "\n\nThought:" onwards
        r"\n\nAction:.*",  # Remove everything from "\n\nAction:" onwards
    ]

    for pattern in cleanup_patterns:
        answer = re.sub(pattern, "", answer, flags=re.DOTALL | re.IGNORECASE)

    # Remove any trailing parenthetical notes like "(Memory_search: ...)"
    answer = re.sub(r"\s*\([^)]*Memory[^)]*\)\s*$", "", answer, flags=re.IGNORECASE)

    # Clean up extra whitespace
    answer = answer.strip()

    # If we ended up with nothing, use the original
    if not answer:
        answer = raw_response.strip()

    return answer


def render_agent_result_simple(result: AgentResult):
    """Simple version without detailed steps for quick responses"""

    if result.memory_context:
        console.print("[bold magenta]🧠 Using memory context...[/bold magenta]")

    # Just show clean final answer
    clean_response = _extract_clean_final_answer(result.final_response)
    console.print(f"[bold green]🤖 {clean_response}[/bold green]")

    # Show simple metadata
    real_tools = [tool for tool in result.tools_used if tool != "_Exception"]
    if real_tools:
        console.print(f"[dim]Tools used: {', '.join(real_tools)}[/dim]")
    if result.memory_context:
        console.print("[dim](Memory: Used)[/dim]")


def render_raw_debug(result: AgentResult):
    """Debug function to show raw data"""
    console.print("[bold red]🐛 DEBUG MODE[/bold red]")
    console.print(f"Raw output: {result.raw_output}")
    console.print(f"Final response: {result.final_response}")
    console.print(f"Tools used: {result.tools_used}")
    console.print(
        f"React steps count: {len(result.react_steps) if result.react_steps else 0}"
    )

    if result.react_steps:
        for i, step in enumerate(result.react_steps):
            console.print(
                f"Step {i}: thought='{step.thought}', action='{step.action}', input='{step.action_input}', obs='{step.observation}', final='{step.final_answer}'"
            )
