# src/cli/render.py

from rich.console import Console
from rich.panel import Panel

from src.shared.agent_result import AgentResult

console = Console()


def render_agent_result(result: AgentResult):
    if result.memory_context:
        console.print("[bold magenta]🤖 Using memory context...[/bold magenta]")

    if result.react_steps:
        for step in result.react_steps:
            if "thought" in step:
                console.print(f"[cyan]🤖 Thought:[/cyan] {step['thought']}")
            if "action" in step:
                console.print(f"[yellow]⚙️ Action:[/yellow] {step['action']}")
            if "observation" in step:
                console.print(f"[green]👁️ Observation:[/green] {step['observation']}")

    console.print(
        Panel.fit(result.final_response, title="💬 Final Answer", style="bold")
    )

    if result.tools_used:
        console.print(f"[dim]Tools used: {', '.join(result.tools_used)}[/dim]")

    if result.memory_context:
        console.print("[dim](Memory: Used)[/dim]")
