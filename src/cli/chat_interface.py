# entity_client/chat_interface.py
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

from src.cli.client import EntityAPIClient

logger = logging.getLogger(__name__)


class ChatInterface:
    """Interactive terminal chat interface with memory awareness"""

    def __init__(self, client: EntityAPIClient, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.current_thread = "default"
        self.local_history = []
        self.console = Console()

        # Setup local history storage if enabled
        if config.get("save_locally", True):
            self.history_path = Path(
                config.get("local_history_path", "./local_chat_history")
            )
            self.history_path.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Start the chat interface"""
        await self._show_welcome()
        await self._chat_loop()

    async def _show_welcome(self):
        """Display enhanced welcome message"""
        self.console.clear()

        # Create welcome panel
        welcome_text = """[bold cyan]🤖 Entity Agent CLI Client[/bold cyan]
[dim]Connected to Entity Agent with PostgreSQL Vector Memory[/dim]"""

        self.console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))

        # Check service health
        health = await self.client.health_check()
        if health.get("status") == "healthy":
            self.console.print(
                f"✅ Connected to service at [green]{self.client.base_url}[/green]"
            )

            # Show features
            features = health.get("features", {})
            if features.get("vector_memory"):
                self.console.print("📊 Vector Memory: [green]Enabled[/green]")
            if features.get("postgresql"):
                self.console.print("🐘 PostgreSQL: [green]Connected[/green]")
        else:
            self.console.print(f"⚠️  Service may be unavailable", style="yellow")

        # Get memory stats
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
        except:
            pass

        # List available tools
        tools = await self.client.list_tools()
        if tools:
            self.console.print(f"\n🛠️  Available tools: [cyan]{', '.join(tools)}[/cyan]")

        # Show commands
        commands_table = Table(title="Commands", show_header=False, box=None)
        commands_table.add_column("Command", style="bold yellow")
        commands_table.add_column("Description")

        commands_table.add_row("exit, quit", "Exit chat")
        commands_table.add_row("history", "Show conversation history")
        commands_table.add_row("memory search <query>", "Search vector memory")
        commands_table.add_row("memory stats", "Show memory statistics")
        commands_table.add_row("thread <id>", "Switch conversation thread")
        commands_table.add_row("tools", "List available tools")
        commands_table.add_row("clear", "Clear screen")
        commands_table.add_row("save", "Save current conversation")

        self.console.print("\n", commands_table)
        self.console.print(f"\n📝 Current thread: [cyan]{self.current_thread}[/cyan]")
        self.console.print("─" * 60 + "\n")

    async def _chat_loop(self):
        """Main chat loop"""
        prompt = self.config.get("prompt", "You: ")

        while True:
            try:
                # Get user input
                user_input = input(prompt).strip()

                # Handle commands
                if await self._handle_command(user_input):
                    continue

                if not user_input:
                    continue

                # Send to agent
                await self._process_message(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n👋 Goodbye!", style="bold green")
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                self.console.print(f"❌ Error: {e}", style="red")

    async def _handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if input was a command."""
        command = user_input.lower()

        if command in ["exit", "quit"]:
            self.console.print("👋 Goodbye!", style="bold green")
            exit(0)

        if command == "clear":
            self.console.clear()
            return True

        if command == "history":
            await self._show_history()
            return True

        if command == "tools":
            await self._show_tools()
            return True

        if command.startswith("memory search "):
            query = user_input[14:].strip()
            if query:
                await self._search_memory(query)
            return True

        if command == "memory stats":
            await self._show_memory_stats()
            return True

        if command.startswith("thread "):
            thread_id = command[7:].strip()
            if thread_id:
                self.current_thread = thread_id
                self.console.print(
                    f"📝 Switched to thread: [cyan]{self.current_thread}[/cyan]"
                )
            return True

        if command == "save":
            await self._save_conversation()
            return True

        return False

    async def _process_message(self, message: str):
        """Process a chat message"""
        try:
            # Show thinking indicator
            if self.config.get("show_timestamps", True):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.console.print(f"\n[dim][{timestamp}][/dim] 🤔 Thinking...")
            else:
                self.console.print("🤔 Thinking...")

            # Send message
            response = await self.client.chat(
                message=message, thread_id=self.current_thread
            )

            # Display response with formatting
            if (
                self.config.get("highlight_memory_responses", True)
                and response.memory_context_used
            ):
                self.console.print(f"\n🤖 [italic]Using memory context...[/italic]")

            self.console.print(f"\n🤖 {response.response}")

            # Show metadata
            metadata_parts = []
            if response.tools_used:
                metadata_parts.append(f"Tools: {', '.join(response.tools_used)}")
            if (
                self.config.get("show_memory_usage", True)
                and response.memory_context_used
            ):
                metadata_parts.append("Memory: Used")

            if metadata_parts:
                self.console.print(f"   [dim]({' | '.join(metadata_parts)})[/dim]")

            # Save to local history
            if self.config.get("save_locally", True):
                self.local_history.append(
                    {
                        "timestamp": response.timestamp.isoformat(),
                        "user_input": message,
                        "agent_output": response.response,
                        "tools_used": response.tools_used,
                        "memory_used": response.memory_context_used,
                    }
                )

            print()  # Add spacing

        except Exception as e:
            self.console.print(f"❌ Failed to get response: {e}", style="red")

    async def _show_history(self):
        """Display conversation history"""
        try:
            logger.debug(f"Fetching history for thread: {self.current_thread}")

            history = await self.client.get_history(self.current_thread, limit=20)

            if not history:
                self.console.print("📚 No conversation history found", style="yellow")
                return

            self.console.print(
                f"\n[bold]📚 History for thread '{self.current_thread}'[/bold]"
            )
            self.console.print("─" * 60)

            for item in history[-10:]:  # Show last 10
                timestamp = item.get("timestamp", "")
                user_input = item.get("user_input", "")
                agent_output = item.get("agent_output", "")
                metadata = item.get("metadata", {})

                if self.config.get("show_timestamps", True):
                    self.console.print(f"\n[dim]{timestamp}[/dim]")

                self.console.print(f"[bold blue]You:[/bold blue] {user_input}")
                self.console.print(f"[bold green]Agent:[/bold green] {agent_output}")

                if metadata.get("memory_used"):
                    self.console.print(
                        "   [dim italic](memory context used)[/dim italic]"
                    )

            self.console.print("─" * 60 + "\n")

            history = await self.client.get_history(self.current_thread, limit=20)
            logger.debug(f"History raw response: {history}")

        except Exception as e:
            self.console.print(f"❌ Failed to get history: {e}", style="red")

    async def _search_memory(self, query: str):
        """Search vector memory"""
        try:
            self.console.print(f"\n🔍 Searching memory for: [cyan]{query}[/cyan]")

            results = await self.client.execute_tool(
                "memory_search",
                {
                    "query": query,
                    "thread_id": self.current_thread,
                    "k": 5,
                },
            )
            memories = results.get("results", [])

            if not memories:
                self.console.print(
                    "No memories found matching your query.", style="yellow"
                )
                return

            self.console.print(f"\nFound {len(memories)} relevant memories:\n")

            for i, memory in enumerate(memories, 1):
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})

                # Create memory panel
                memory_text = f"{content}\n\n[dim]Type: {metadata.get('memory_type', 'unknown')} | "
                memory_text += (
                    f"Importance: {metadata.get('importance_score', 0):.1f}[/dim]"
                )

                self.console.print(
                    Panel(memory_text, title=f"Memory {i}", border_style="blue")
                )

        except Exception as e:
            self.console.print(f"❌ Memory search failed: {e}", style="red")

    async def _show_memory_stats(self):
        """Display memory statistics"""
        try:
            stats = await self.client.get_memory_stats()

            # Create stats table
            table = Table(
                title="Memory Statistics", show_header=True, header_style="bold cyan"
            )
            table.add_column("Metric", style="dim")
            table.add_column("Value", justify="right")

            table.add_row("Total Memories", str(stats.get("total_memories", 0)))
            table.add_row(
                "Total Conversations", str(stats.get("total_conversations", 0))
            )
            table.add_row("Backend", stats.get("backend", "unknown"))
            table.add_row("Embedding Model", stats.get("embedding_model", "unknown"))
            table.add_row("Vector Dimensions", str(stats.get("vector_dimensions", 0)))

            self.console.print("\n", table)

            # Show memory types
            memory_types = stats.get("memory_types", {})
            if memory_types:
                self.console.print("\n[bold]Memory Types:[/bold]")
                for mtype, count in memory_types.items():
                    self.console.print(f"  {mtype}: [cyan]{count}[/cyan]")

            # Show top topics
            topics = stats.get("top_topics", {})
            if topics:
                self.console.print("\n[bold]Top Topics:[/bold]")
                for topic, count in list(topics.items())[:5]:
                    self.console.print(f"  {topic}: [cyan]{count}[/cyan]")

        except Exception as e:
            self.console.print(f"❌ Failed to get memory stats: {e}", style="red")

    async def _show_tools(self):
        """Display available tools"""
        try:
            tools = await self.client.list_tools()

            if not tools:
                self.console.print("🛠️  No tools available", style="yellow")
                return

            table = Table(title="Available Tools", show_header=False, box=None)
            table.add_column("Tool", style="bold cyan")

            for tool in tools:
                table.add_row(f"• {tool}")

            self.console.print("\n", table, "\n")

        except Exception as e:
            self.console.print(f"❌ Failed to get tools: {e}", style="red")

    async def _save_conversation(self):
        """Save current conversation to file"""
        if not self.local_history:
            self.console.print("💾 No conversation to save", style="yellow")
            return

        try:
            filename = f"chat_{self.current_thread}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.history_path / filename

            with open(filepath, "w") as f:
                json.dump(self.local_history, f, indent=2, default=str)

            self.console.print(f"💾 Conversation saved to: [green]{filepath}[/green]")

        except Exception as e:
            self.console.print(f"❌ Failed to save conversation: {e}", style="red")

    async def run(self):
        """Entry point for `main.py chat` or `main.py both` mode"""
        await self.start()
