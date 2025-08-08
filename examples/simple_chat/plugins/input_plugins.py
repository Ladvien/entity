"""Input stage plugins for simple chat agent."""

from typing import Any, Dict

from pydantic import BaseModel

from entity.plugins.input_adapter import InputAdapterPlugin
from entity.resources.logging import LogCategory, LogLevel
from entity.workflow.executor import WorkflowExecutor


class ChatInputPlugin(InputAdapterPlugin):
    """Process user chat input with context and history management."""

    class ConfigModel(BaseModel):
        """Configuration for chat input processing."""

        max_history_length: int = 50
        preserve_context: bool = True
        enable_system_commands: bool = True

    supported_stages = [WorkflowExecutor.INPUT]

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.validate_config()

    async def _execute_impl(self, context) -> str:
        """Process user input and maintain conversation history."""
        logger = context.get_resource("logging")

        await logger.log(
            LogLevel.DEBUG,
            LogCategory.PLUGIN_LIFECYCLE,
            "Processing chat input",
            plugin_name=self.__class__.__name__,
        )

        user_message = context.message or ""
        user_id = context.user_id or "default"

        # Handle system commands
        if self.config.enable_system_commands and user_message.startswith("/"):
            await self._handle_system_command(context, user_message)
            return user_message

        # Get conversation history
        history_key = f"chat_history:{user_id}"
        chat_history = await context.recall(history_key, [])

        # Add user message to history
        chat_history.append(
            {"role": "user", "content": user_message, "timestamp": context.execution_id}
        )

        # Maintain history length
        if len(chat_history) > self.config.max_history_length:
            chat_history = chat_history[-self.config.max_history_length :]

        # Store updated history
        await context.remember(history_key, chat_history)

        # Store current input for other plugins
        await context.remember("current_input", user_message)
        await context.remember("input_processed", True)

        await logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "User input processed",
            message_length=len(user_message),
            history_length=len(chat_history),
        )

        return user_message

    async def _handle_system_command(self, context, command: str) -> None:
        """Handle system commands like /help, /clear, etc."""
        logger = context.get_resource("logging")

        if command == "/clear":
            user_id = context.user_id or "default"
            await context.remember(f"chat_history:{user_id}", [])
            await context.remember("system_message", "Chat history cleared.")

        elif command == "/help":
            help_text = """Available commands:
/help - Show this help message
/clear - Clear chat history
/status - Show agent status
"""
            await context.remember("system_message", help_text)

        elif command == "/status":
            user_id = context.user_id or "default"
            history = await context.recall(f"chat_history:{user_id}", [])
            status = f"Chat agent active. History: {len(history)} messages."
            await context.remember("system_message", status)

        await logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "System command processed",
            command=command,
        )
