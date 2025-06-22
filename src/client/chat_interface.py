"""
Enhanced terminal chat interface with memory features
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from src.client.client import EntityAPIClient
from src.client.render import AgentResultRenderer


logger = logging.getLogger(__name__)


class ChatInterface:
    """Interactive terminal chat interface with memory awareness"""

    def __init__(self, client: EntityAPIClient, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.current_thread = "default"
        self.local_history = []
        self.console = Console()
        self.prompt = "[bold cyan]You:[/bold cyan] "

        if config.get("save_locally", True):
            self.history_path = Path(
                config.get("local_history_path", "./local_chat_history")
            )
            self.history_path.mkdir(parents=True, exist_ok=True)

    async def run(self):
        await self.start()

    async def start(self):
        await self._show_welcome()
        await self._chat_loop()

    async def _chat_loop(self):
        while True:
            try:
                user_input = self.console.input(self.prompt).strip()
                if not user_input:
                    continue

                if user_input.lower() in {"exit", "quit"}:
                    self.console.print("👋 Goodbye.", style="bold green")
                    break

                agent_result = await self.client.chat(
                    user_input, thread_id=self.current_thread
                )

                renderer = AgentResultRenderer(agent_result)

                if self.config.get("debug_mode", False):
                    self.console.print("[bold red]🐛 DEBUG MODE ACTIVE[/bold red]")
                    renderer.render_debug()
                elif (
                    self.config.get("show_react_steps", True)
                    and agent_result.react_steps
                ):
                    renderer.render()
                else:
                    renderer.render_simple()

                if self.config.get("save_locally", True):
                    self.local_history.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "user_input": user_input,
                            "agent_output": agent_result.final_response,
                            "tools_used": agent_result.tools_used,
                            "memory_used": bool(agent_result.memory_context.strip()),
                            "react_steps_count": len(agent_result.react_steps or []),
                        }
                    )
                print()

            except Exception as e:
                logger.exception("❌ Chat error")
                self.console.print(f"❌ Error: {e}", style="red")

    async def _show_welcome(self):
        self.console.clear()
        welcome_text = """[bold cyan]🤖 Entity Agent CLI Client[/bold cyan]
[dim]Connected to Entity Agent with PostgreSQL Vector Memory[/dim]"""
        self.console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))

        health = await self.client.health_check()
        if health.get("status") == "healthy":
            self.console.print(
                f"✅ Connected to service at [green]{self.client.base_url}[/green]"
            )
            features = health.get("features", {})
            if features.get("vector_memory"):
                self.console.print("📊 Vector Memory: [green]Enabled[/green]")
            if features.get("postgresql"):
                self.console.print("🐘 PostgreSQL: [green]Connected[/green]")
        else:
            self.console.print(f"⚠️  Service may be unavailable", style="yellow")

        try:
            memory_stats = await self.client.get_memory_stats()
            if memory_stats:
                self.console.print(f"\n💾 Memory Stats:")
                self.console.print(
                    f"   Total Memories: [cyan]{memory_stats.get('total_memories', 0)}[/cyan]"
                )
                self.console.print(
                    f"   Conversations: [cyan]{memory_stats.get('total_conversations', 0)}[/cyan]"
                )
                self.console.print(
                    f"   Embedding Model: [dim]{memory_stats.get('embedding_model', 'unknown')}[/dim]"
                )
        except Exception as e:
            logger.warning(f"Could not fetch memory stats: {e}")

        tools = await self.client.list_tools()
        if tools:
            self.console.print(f"\n🛠️  Available tools: [cyan]{', '.join(tools)}[/cyan]")

        commands_table = Table(title="Commands", show_header=False, box=None)
        commands_table.add_column("Command", style="bold yellow")
        commands_table.add_column("Description")

        commands_table.add_row("exit, quit", "Exit chat")
        commands_table.add_row("help", "Show help message")

        self.console.print()
        self.console.print(commands_table)
        self.console.print(f"\n📝 Current thread: [cyan]{self.current_thread}[/cyan]")
        self.console.print("─" * 60 + "\n")
