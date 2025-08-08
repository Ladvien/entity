"""Thinking stage plugins for simple chat agent."""

from typing import Any, Dict

from pydantic import BaseModel

from entity.plugins.prompt import PromptPlugin
from entity.resources.logging import LogCategory, LogLevel
from entity.workflow.executor import WorkflowExecutor


class ChatReasoningPlugin(PromptPlugin):
    """Generate contextual responses based on conversation history."""

    class ConfigModel(BaseModel):
        """Configuration for chat reasoning."""

        personality: str = "helpful and friendly"
        response_style: str = "conversational"
        max_context_messages: int = 10
        include_thinking: bool = False

    supported_stages = [WorkflowExecutor.THINK]
    dependencies = ["llm"]

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.validate_config()

    async def _execute_impl(self, context) -> str:
        """Generate a thoughtful response based on context."""
        logger = context.get_resource("logging")
        llm = context.get_resource("llm")

        await logger.log(
            LogLevel.DEBUG,
            LogCategory.PLUGIN_LIFECYCLE,
            "Starting chat reasoning",
            plugin_name=self.__class__.__name__,
        )

        # Check for system messages first
        system_message = await context.recall("system_message", None)
        if system_message:
            await context.remember("response", system_message)
            await context.remember("system_message", None)  # Clear it
            return context.message or ""

        user_message = await context.recall("current_input", "")
        user_id = context.user_id or "default"

        # Get recent conversation history for context
        history_key = f"chat_history:{user_id}"
        full_history = await context.recall(history_key, [])

        # Limit context to recent messages
        recent_history = (
            full_history[-self.config.max_context_messages :] if full_history else []
        )

        # Build conversation context
        conversation_context = ""
        if recent_history:
            conversation_context = "Recent conversation:\\n"
            for msg in recent_history[:-1]:  # Exclude the current message
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role.title()}: {content}\\n"

        # Create reasoning prompt
        thinking_prompt = f"""You are a {self.config.personality} AI assistant.
Your response style is {self.config.response_style}.

{conversation_context}

Current user message: {user_message}

Please provide a helpful, contextual response that:
1. Acknowledges the conversation history if relevant
2. Directly addresses the user's current message
3. Is appropriate for the {self.config.response_style} style
4. Maintains a {self.config.personality} tone

Response:"""

        # Generate response using LLM
        llm_response = await llm.generate(thinking_prompt)
        response_text = (
            llm_response.content
            if hasattr(llm_response, "content")
            else str(llm_response)
        )

        # Store reasoning and response
        if self.config.include_thinking:
            await context.remember(
                "thinking_process",
                {
                    "context_messages": len(recent_history),
                    "reasoning_prompt": thinking_prompt,
                    "personality": self.config.personality,
                    "style": self.config.response_style,
                },
            )

        await context.remember("response", response_text)

        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Chat response generated",
            response_length=len(response_text),
            context_messages=len(recent_history),
        )

        return context.message or ""


class ContextAnalyzerPlugin(PromptPlugin):
    """Analyze conversation context and user intent."""

    class ConfigModel(BaseModel):
        """Configuration for context analysis."""

        analyze_sentiment: bool = True
        detect_topics: bool = True
        track_preferences: bool = True

    supported_stages = [WorkflowExecutor.THINK]
    dependencies = ["llm"]

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.validate_config()

    async def _execute_impl(self, context) -> str:
        """Analyze conversation context and user patterns."""
        logger = context.get_resource("logging")
        llm = context.get_resource("llm")

        user_message = await context.recall("current_input", "")
        user_id = context.user_id or "default"

        # Get conversation history for analysis
        history_key = f"chat_history:{user_id}"
        chat_history = await context.recall(history_key, [])

        analysis = {}

        if self.config.analyze_sentiment and user_message:
            sentiment_prompt = f"Analyze the sentiment of this message (positive/negative/neutral): {user_message}"
            sentiment_response = await llm.generate(sentiment_prompt)
            analysis["sentiment"] = (
                sentiment_response.content
                if hasattr(sentiment_response, "content")
                else "neutral"
            )

        if self.config.detect_topics and chat_history:
            recent_messages = [msg.get("content", "") for msg in chat_history[-5:]]
            topics_prompt = f"What are the main topics in this conversation? Messages: {recent_messages}"
            topics_response = await llm.generate(topics_prompt)
            analysis["topics"] = (
                topics_response.content if hasattr(topics_response, "content") else ""
            )

        # Store analysis for use by other plugins
        await context.remember("context_analysis", analysis)

        await logger.log(
            LogLevel.DEBUG,
            LogCategory.PLUGIN_LIFECYCLE,
            "Context analysis completed",
            sentiment=analysis.get("sentiment", "unknown"),
            topics_detected=bool(analysis.get("topics")),
        )

        return context.message or ""
