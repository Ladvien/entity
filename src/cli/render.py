from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
import re

from src.shared.agent_result import AgentResult


class AgentResultRenderer:
    def __init__(self, result: AgentResult, console: Console = Console()):
        self.result = result
        self.console = console

    def render(self):
        self._render_memory_context()
        self._render_react_steps()
        self._render_final_answer()
        self._render_metadata()

    def render_simple(self):
        if self.result.memory_context:
            self.console.print(
                "[bold magenta]🧠 Using memory context...[/bold magenta]"
            )

        clean = self._extract_clean_final_answer(self.result.final_response)
        self.console.print(f"[bold green]🤖 {clean}[/bold green]")

        tools = [t for t in self.result.tools_used or [] if t != "_Exception"]
        if tools:
            self.console.print(f"[dim]Tools used: {', '.join(tools)}[/dim]")

        if self.result.memory_context:
            self.console.print("[dim](Memory: Used)[/dim]")

    def render_debug(self):
        self.console.print("[bold red]🐛 DEBUG MODE[/bold red]")
        self.console.print(f"Raw output: {self.result.raw_output}")
        self.console.print(f"Final response: {self.result.final_response}")
        self.console.print(f"Tools used: {self.result.tools_used}")
        self.console.print(f"ReAct steps: {len(self.result.react_steps or [])}")

        for i, step in enumerate(self.result.react_steps or []):
            self.console.print(
                f"Step {i}: thought='{step.thought}', action='{step.action}', "
                f"input='{step.action_input}', obs='{step.observation}', "
                f"final='{step.final_answer}'"
            )

    def _render_memory_context(self):
        if self.result.memory_context:
            self.console.print(
                "\n[bold magenta]🧠 Using memory context...[/bold magenta]\n"
            )

    def _render_react_steps(self):
        if not self.result.react_steps:
            return

        self.console.print("[bold blue]🔄 Agent Reasoning Process:[/bold blue]\n")

        for i, step in enumerate(self.result.react_steps, 1):
            if i > 1:
                self.console.print(Rule(style="dim"))
                self.console.print()

            self.console.print(f"[dim]Step {i}:[/dim]")

            step_text = Text()
            if step.thought:
                step_text.append("🤔 Thought: ", style="cyan bold")
                step_text.append(f"{step.thought.strip()}\n", style="cyan")
            if step.action:
                step_text.append("⚙️ Action: ", style="yellow bold")
                step_text.append(f"{step.action.strip()}\n", style="yellow")
            if step.action_input:
                step_text.append("📝 Action Input: ", style="magenta bold")
                step_text.append(f"{step.action_input.strip()}\n", style="magenta")
            if step.observation:
                step_text.append("👁️ Observation: ", style="green bold")
                step_text.append(f"{step.observation.strip()}\n", style="green")

            self.console.print(
                step_text if step_text.plain else "[dim]Empty step[/dim]"
            )
            self.console.print()

    def _render_final_answer(self):
        clean = self._extract_clean_final_answer(self.result.final_response)
        self.console.print(
            Panel.fit(
                clean,
                title="💬 Final Answer",
                style="bold green",
                border_style="green",
            )
        )

    def _render_metadata(self):
        parts = []

        tools = [t for t in self.result.tools_used or [] if t != "_Exception"]
        if tools:
            parts.append(f"🛠️ Tools: {', '.join(tools)}")

        if self.result.memory_context:
            parts.append("🧠 Memory: Used")

        if self.result.token_count:
            parts.append(f"🔢 Tokens: {self.result.token_count}")

        if parts:
            self.console.print(f"[dim]   {' | '.join(parts)}[/dim]")

    def _extract_clean_final_answer(self, raw: str) -> str:
        match = re.search(r"Final Answer:\s*(.*)", raw, re.DOTALL | re.IGNORECASE)
        answer = match.group(1).strip() if match else raw.strip()

        cleanup_patterns = [
            r"\n\n?Question:.*",
            r"\n\n?Thought:.*",
            r"\n\n?Action:.*",
        ]
        for pattern in cleanup_patterns:
            answer = re.sub(pattern, "", answer, flags=re.DOTALL | re.IGNORECASE)

        answer = re.sub(r"\s*\([^)]*Memory[^)]*\)\s*$", "", answer, flags=re.IGNORECASE)
        return answer.strip() or raw.strip()
