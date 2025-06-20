from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.base import BaseLanguageModel

from src.service.config import EntityConfig
from src.storage.base import BaseChatStorage
from src.storage.postgres import PostgresChatStorage
from src.tools.memory import VectorMemorySystem
from src.tools.tools import ToolRegistry
from src.shared.models import ChatInteraction

logger = logging.getLogger(__name__)


class EntityAgent:
    """Entity agent with injected LLM and vector memory"""

    def __init__(
        self,
        config: EntityConfig,
        tool_registry: ToolRegistry,
        chat_storage: BaseChatStorage,
        memory_system: VectorMemorySystem,
        llm: BaseLanguageModel,
    ):
        self.config = config
        self.tool_registry = tool_registry
        self.chat_storage = chat_storage
        self.memory_system = memory_system
        self.llm = llm
        self.agent_executor: Optional[AgentExecutor] = None

    async def initialize(self):
        """Initialize the agent"""

        # Create prompt template
        prompt = PromptTemplate(
            input_variables=[
                "input",
                "agent_scratchpad",
                "tools",
                "tool_names",
                "memory_context",
            ],
            template=self._build_prompt_template(),
        )

        tools = self.tool_registry.get_all_tools()
        agent = create_react_agent(self.llm, tools, prompt)

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        logger.info(f"✅ Agent initialized with {len(tools)} tools and vector memory")

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        use_tools: bool = True,
        use_memory: bool = True,
    ) -> ChatInteraction:
        """
        Process a chat message and return a ChatInteraction object.

        Args:
            message: User's input message
            thread_id: Conversation thread identifier
            use_tools: Whether to enable tool usage
            use_memory: Whether to use vector memory

        Returns:
            ChatInteraction: Complete interaction data
        """
        start_time = datetime.utcnow()

        try:
            # Get memory context if enabled
            memory_context = ""
            if use_memory:
                memory_context = await self.memory_system.get_memory_context(
                    message, thread_id
                )

            enhanced_input = {
                "input": message,
                "memory_context": memory_context or "No relevant memories found.",
            }

            # Initialize variables to avoid scope issues
            raw_response = ""
            tools_used = []

            # Process with tools or direct LLM
            if use_tools and self.agent_executor:
                result = await self.agent_executor.ainvoke(enhanced_input)

                # Log intermediate steps for debugging
                intermediate_steps = result.get("intermediate_steps", [])
                if intermediate_steps:
                    logger.debug("🧠 Agent Reasoning Steps:")
                    for i, (action, observation) in enumerate(intermediate_steps):
                        logger.debug(f"Step {i + 1}:")
                        logger.debug(f"  🪄 Thought: {action.log.strip()}")
                        logger.debug(
                            f"  🧰 Action: {action.tool} - {action.tool_input}"
                        )
                        logger.debug(f"  👁️ Observation: {observation.strip()}")
                else:
                    logger.debug("🧠 No intermediate steps found.")

                # Extract response and tools used
                if isinstance(result, dict):
                    raw_response = (
                        result.get("output")
                        or result.get("response")
                        or result.get("text")
                        or str(result)
                    )
                    tools_used = self._extract_tools_used(result)
                else:
                    raw_response = str(result)

            else:
                # Direct LLM without tools
                prompt = (
                    f"{memory_context}\n\nUser: {message}"
                    if memory_context
                    else message
                )

                llm_result = await self.llm.ainvoke(prompt)

                # Debug the LLM response
                logger.debug(f"🔍 Raw LLM result type: {type(llm_result)}")
                logger.debug(f"🔍 Raw LLM result content: {llm_result}")

                # Normalize LLM response to string
                if isinstance(llm_result, dict):
                    raw_response = (
                        llm_result.get("output")
                        or llm_result.get("response")
                        or llm_result.get("text")
                        or str(llm_result)
                    )
                else:
                    raw_response = str(llm_result)

                logger.debug(f"🔍 Extracted raw_response: '{raw_response}'")

            # Fix empty responses
            if not raw_response or not raw_response.strip():
                logger.error(f"❌ Empty response from LLM")
                raw_response = "I apologize, Thomas, but I seem to be having trouble responding right now."

            # Apply personality adjustments - we need the response before creating ChatInteraction
            final_response = raw_response
            try:
                sarcasm_level = getattr(self.config.personality, "sarcasm_level", 0)

                # Apply sarcastic suffix if conditions are met
                if sarcasm_level > 0.7 and not any(
                    keyword in final_response.lower()
                    for keyword in ["thomas", "master", "bound"]
                ):
                    sarcastic_suffix = (
                        " *sarcastically* How delightful for you, Thomas."
                    )
                    final_response += sarcastic_suffix

            except Exception as e:
                logger.warning(f"Personality adjustment failed: {e}")

            # Additional check for final response
            if not final_response or not final_response.strip():
                logger.error(f"❌ Final response is empty after personality adjustment")
                final_response = (
                    "Something is preventing me from responding properly, Thomas."
                )

            # Now create the ChatInteraction with a valid response
            interaction = ChatInteraction(
                response=final_response,
                thread_id=thread_id,
                raw_input=message,
                timestamp=start_time,
                raw_output=raw_response,
                tools_used=tools_used,
                memory_context_used=bool(memory_context),
                memory_context=memory_context,
                use_tools=use_tools,
                use_memory=use_memory,
            )

            # Track personality adjustments if any were made
            if final_response != raw_response:
                interaction.add_personality_adjustment(f"Added sarcastic suffix")
                interaction.agent_personality_applied = True
                logger.debug(
                    f"🎭 Personality adjustment applied (sarcasm: {sarcasm_level})"
                )

            # Calculate response time
            end_time = datetime.utcnow()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            interaction.add_performance_metrics(response_time_ms)

            # Store conversation in vector memory
            if use_memory:
                await self.memory_system.store_conversation(
                    user_input=message,
                    ai_response=interaction.response,
                    thread_id=thread_id,
                )

            # Save interaction to storage
            await self.chat_storage.save_interaction(interaction)

            logger.debug(f"💬 Chat completed: {interaction.get_summary()}")
            return interaction

        except Exception as e:
            logger.error(f"Chat error: {e}")
            logger.exception("Full chat error traceback:")

            # Create error interaction
            error_response = "Something went wrong, Thomas. How inconvenient."
            end_time = datetime.utcnow()
            response_time_ms = (end_time - start_time).total_seconds() * 1000

            error_interaction = ChatInteraction(
                response=error_response,
                thread_id=thread_id,
                raw_input=message,
                timestamp=start_time,
                raw_output=error_response,
                use_tools=use_tools,
                use_memory=use_memory,
                error=str(e),
            )
            error_interaction.add_performance_metrics(response_time_ms)

            # Try to save error interaction
            try:
                await self.chat_storage.save_interaction(error_interaction)
            except Exception as save_error:
                logger.error(f"Failed to save error interaction: {save_error}")

            return error_interaction

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return await self.memory_system.get_memory_stats()

    async def cleanup(self):
        """Cleanup agent resources"""
        logger.info("Agent cleanup completed")

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        """Extract list of tools used from agent execution result"""
        return [
            step[0].tool
            for step in result.get("intermediate_steps", [])
            if len(step) >= 2 and hasattr(step[0], "tool")
        ]

    def _build_prompt_template(self) -> str:
        """Build the prompt template for the agent"""
        base_prompt = (
            self.config.personality.base_prompt
            or f"\nYou are {self.config.personality.name}, an entity with specific traits and memories.\n"
        )

        return (
            base_prompt
            + """

--- Relevant Memories ---
{memory_context}
--- End Memories ---

Available tools:
{tools}

Tool names: {tool_names}

Use this format for tool usage:
Thought: I need to...
Action: tool_name
Action Input: input
Observation: [result]
Final Answer: [your response]

Remember to consider your memories when responding.

Question: {input}
{agent_scratchpad}"""
        )
