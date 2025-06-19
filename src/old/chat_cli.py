# src/cli/chat.py
"""
Interactive CLI chat interface with clean separation of concerns.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ChatCLI:
    """
    Interactive chat CLI with clean command handling.
    """

    def __init__(self, app_service: ApplicationService):
        self.app_service = app_service
        self.current_thread = "default"

    async def start(self) -> None:
        """Start the interactive chat loop."""
        logger.info("🤖 Entity Agent Chat Loop Started")

        # Wait for initialization
        while not self.app_service.is_initialized:
            await asyncio.sleep(0.1)

        await self._show_welcome()
        await self._chat_loop()

    async def _show_welcome(self) -> None:
        """Display welcome message and available commands."""
        config = self.app_service.config
        memory_status = (
            "with Memory" if self.app_service.has_memory() else "without memory"
        )

        print(f"\n🎭 Welcome! You are now talking to {config.entity.name}")
        print(
            f"📊 Personality: Sarcasm {config.entity.sarcasm_level:.1f}, Loyalty {config.entity.loyalty_level:.1f}"
        )
        print(f"💾 Running {memory_status}")
        print("\n💡 Commands:")
        print("   'exit' or 'quit' - Exit chat")

        if self.app_service.has_memory():
            print("   'history' - Show conversation history")
            print("   'clear' - Clear current conversation")
            print("   'switch <thread_id>' - Switch to different conversation thread")
            print("   'memory' - Show memory statistics")
            print(f"📝 Current thread: {self.current_thread}")

        print("   'status' - Show agent status")
        print("   'config' - Show current configuration")
        print()

    async def _chat_loop(self) -> None:
        """Main chat loop with command processing."""
        while True:
            try:
                user_input = input("You: ").strip()

                if await self._handle_command(user_input):
                    continue

                if not user_input:
                    continue

                await self._process_chat_message(user_input)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Chat loop error: {e}")
                print(f"❌ Error: {e}")

    async def _handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if input was a command."""
        command = user_input.lower()

        if command in ["exit", "quit"]:
            print("👋 Goodbye!")
            return True

        if command == "status":
            await self._show_status()
            return True

        if command == "config":
            await self._show_config()
            return True

        if self.app_service.has_memory():
            if command == "memory":
                await self._show_memory_stats()
                return True

            if command == "history":
                await self._show_history()
                return True

            if command == "clear":
                await self._clear_history()
                return True

            if command.startswith("switch "):
                await self._switch_thread(command[7:].strip())
                return True

        return False

    async def _process_chat_message(self, message: str) -> None:
        """Process a regular chat message."""
        print("🤖 Thinking...")
        response = await self.app_service.process_chat(message, self.current_thread)
        print(f"{self.app_service.config.entity.name}: {response}")
        print()

    async def _show_status(self) -> None:
        """Show current agent status."""
        status = self.app_service.get_status()
        config = self.app_service.config

        print(f"🤖 Entity Agent Status:")
        print(f"   Entity: {status['entity_name']} ({status['entity_id']})")
        print(f"   Ollama: {config.ollama.model} @ {config.ollama.base_url}")
        print(f"   Database: {config.database.host}:{config.database.port}")
        print(f"   Memory: {'Available' if status['has_memory'] else 'None'}")
        print(f"   Thread: {self.current_thread if status['has_memory'] else 'N/A'}")
        print(f"   Debug: {config.debug}")

    async def _show_config(self) -> None:
        """Show current configuration."""
        config = self.app_service.config

        print(f"🔧 Current Configuration:")
        print(f"   Entity ID: {config.entity.entity_id}")
        print(f"   Entity Name: {config.entity.name}")
        print(f"   Sarcasm Level: {config.entity.sarcasm_level}")
        print(f"   Loyalty Level: {config.entity.loyalty_level}")
        print(f"   Anger Level: {config.entity.anger_level}")
        print(f"   Wit Level: {config.entity.wit_level}")
        print(f"   Response Brevity: {config.entity.response_brevity}")
        print(f"   Memory Influence: {config.entity.memory_influence}")
        print(f"   Ollama Model: {config.ollama.model}")
        print(f"   Ollama URL: {config.ollama.base_url}")
        print(
            f"   Database: {config.database.host}:{config.database.port}/{config.database.name}"
        )

    async def _show_memory_stats(self) -> None:
        """Show memory statistics."""
        try:
            stats = await self.app_service.get_memory_stats()
            print(f"🧠 Memory Statistics:")
            print(f"   Total memories: {stats.get('total_memories', 0)}")
            print(f"   Total conversations: {stats.get('total_conversations', 0)}")
            print(f"   Memory types: {stats.get('memory_types', {})}")
            print(f"   Emotions: {stats.get('emotions', {})}")
            print(
                f"   Top topics: {dict(list(stats.get('top_topics', {}).items())[:5])}"
            )
            print(f"   Backend: {stats.get('backend', 'unknown')}")
        except Exception as e:
            print(f"❌ Error getting memory stats: {e}")

    async def _show_history(self) -> None:
        """Show conversation history."""
        conversations = await self.app_service.get_conversation_history(
            self.current_thread, limit=10
        )
        if conversations:
            print(f"📚 History for thread '{self.current_thread}':")
            for line in conversations[-10:]:
                content = line[:80] + "..." if len(line) > 80 else line
                print(f"   💬 {content}")
        else:
            print("📚 No conversation history found")

    async def _clear_history(self) -> None:
        """Clear conversation history."""
        success = await self.app_service.delete_conversation(self.current_thread)
        if success:
            print(f"🧹 Conversation history cleared for thread '{self.current_thread}'")
        else:
            print("❌ Failed to clear conversation history")

    async def _switch_thread(self, new_thread: str) -> None:
        """Switch to a different conversation thread."""
        if new_thread:
            self.current_thread = new_thread
            print(f"📝 Switched to thread: {self.current_thread}")
        else:
            print("❌ Please specify a thread ID")
