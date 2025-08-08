"""Output stage plugins for simple chat agent."""

from typing import Any, Dict

from pydantic import BaseModel

from entity.plugins.output_adapter import OutputAdapterPlugin
from entity.resources.logging import LogCategory, LogLevel
from entity.workflow.executor import WorkflowExecutor


class ChatOutputPlugin(OutputAdapterPlugin):
    """Format and deliver chat responses with conversation management."""

    class ConfigModel(BaseModel):
        """Configuration for chat output."""

        format_style: str = "plain"  # plain, markdown, rich
        include_metadata: bool = False
        add_to_history: bool = True
        show_thinking: bool = False

    supported_stages = [WorkflowExecutor.OUTPUT]

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.validate_config()

    async def _execute_impl(self, context) -> str:
        """Format and deliver the final response."""
        logger = context.get_resource("logging")

        await logger.log(
            LogLevel.DEBUG,
            LogCategory.PLUGIN_LIFECYCLE,
            "Formatting chat output",
            plugin_name=self.__class__.__name__,
        )

        # Get the generated response
        response = await context.recall(
            "response", "I'm sorry, I couldn't generate a response."
        )
        user_id = context.user_id or "default"

        # Format response based on style
        if self.config.format_style == "markdown":
            formatted_response = f"**Assistant:** {response}"
        elif self.config.format_style == "rich":
            formatted_response = f"🤖 {response}"
        else:
            formatted_response = response

        # Add metadata if requested
        if self.config.include_metadata:
            context_analysis = await context.recall("context_analysis", {})
            if context_analysis:
                sentiment = context_analysis.get("sentiment", "unknown")
                formatted_response += f"\\n\\n_[Sentiment: {sentiment}]_"

        # Show thinking process if requested
        if self.config.show_thinking:
            thinking = await context.recall("thinking_process", {})
            if thinking:
                formatted_response += f"\\n\\n<details>\\n<summary>Thinking Process</summary>\\n\\nPersonality: {thinking.get('personality', 'N/A')}\\nStyle: {thinking.get('style', 'N/A')}\\nContext Messages: {thinking.get('context_messages', 0)}\\n</details>"

        # Add assistant response to conversation history
        if self.config.add_to_history:
            history_key = f"chat_history:{user_id}"
            chat_history = await context.recall(history_key, [])

            chat_history.append(
                {
                    "role": "assistant",
                    "content": response,  # Store unformatted response in history
                    "timestamp": context.execution_id,
                }
            )

            await context.remember(history_key, chat_history)

        await logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Chat response delivered",
            response_length=len(formatted_response),
            format_style=self.config.format_style,
        )

        return formatted_response


class ConversationSummaryPlugin(OutputAdapterPlugin):
    """Provide conversation summaries and insights."""

    class ConfigModel(BaseModel):
        """Configuration for conversation summaries."""

        summary_trigger_length: int = 20  # Messages before summarizing
        auto_summarize: bool = False
        include_insights: bool = True

    supported_stages = [WorkflowExecutor.OUTPUT]
    dependencies = ["llm"]

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.validate_config()

    async def _execute_impl(self, context) -> str:
        """Generate conversation summaries when appropriate."""
        logger = context.get_resource("logging")
        llm = context.get_resource("llm")

        user_id = context.user_id or "default"
        history_key = f"chat_history:{user_id}"
        chat_history = await context.recall(history_key, [])

        # Check if we should summarize
        should_summarize = (
            self.config.auto_summarize
            and len(chat_history) >= self.config.summary_trigger_length
        )

        # Or if user requested summary
        current_input = await context.recall("current_input", "")
        user_requested_summary = any(
            keyword in current_input.lower()
            for keyword in ["summarize", "summary", "recap"]
        )

        if should_summarize or user_requested_summary:
            await self._generate_summary(context, chat_history, llm, logger)

        # Return the main response (this plugin augments, doesn't replace)
        return await context.recall("response", "")

    async def _generate_summary(self, context, history: list, llm, logger) -> None:
        """Generate and store conversation summary."""
        if not history:
            return

        # Prepare conversation text
        conversation_text = ""
        for msg in history[-self.config.summary_trigger_length :]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation_text += f"{role.title()}: {content}\\n"

        # Generate summary
        summary_prompt = f"""Summarize this conversation, highlighting key topics and insights:

{conversation_text}

Provide a concise summary that captures:
1. Main topics discussed
2. Key information exchanged
3. Any requests or tasks mentioned
4. Overall conversation flow

Summary:"""

        summary_response = await llm.generate(summary_prompt)
        summary = (
            summary_response.content
            if hasattr(summary_response, "content")
            else str(summary_response)
        )

        # Store summary
        user_id = context.user_id or "default"
        await context.remember(
            f"conversation_summary:{user_id}",
            {
                "summary": summary,
                "message_count": len(history),
                "generated_at": context.execution_id,
            },
        )

        # If user requested it, add to response
        current_input = await context.recall("current_input", "")
        if any(
            keyword in current_input.lower()
            for keyword in ["summarize", "summary", "recap"]
        ):
            current_response = await context.recall("response", "")
            enhanced_response = (
                f"{current_response}\\n\\n**Conversation Summary:**\\n{summary}"
            )
            await context.remember("response", enhanced_response)

        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Conversation summary generated",
            summary_length=len(summary),
            messages_summarized=len(history),
        )
