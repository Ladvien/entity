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
from src.tools.tools import ToolManager
from src.shared.models import ChatInteraction

logger = logging.getLogger(__name__)


class EntityAgent:
    """Entity agent with injected LLM and vector memory"""

    def __init__(
        self,
        config: EntityConfig,
        tool_manager: ToolManager,
        chat_storage: BaseChatStorage,
        memory_system: VectorMemorySystem,
        llm: BaseLanguageModel,
    ):
        self.config = config
        self.tool_registry = tool_manager
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
            verbose=True,  # Enable verbose logging to see agent thoughts
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="generate",  # Stop when final answer is generated
        )

        logger.info(f"✅ Agent initialized with {len(tools)} tools and vector memory")
        logger.info(f"🛠️ Available tools: {[tool.name for tool in tools]}")

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        use_tools: bool = True,
        use_memory: bool = True,
    ) -> ChatInteraction:
        start_time = datetime.utcnow()
        raw_response = ""
        tools_used = []
        token_count = 0
        memory_context = ""

        logger.info(
            f"💬 Processing message: '{message[:100]}{'...' if len(message) > 100 else ''}'"
        )
        logger.info(
            f"🎛️ Settings - Tools: {use_tools}, Memory: {use_memory}, Thread: {thread_id}"
        )

        try:
            # Fetch memory context if enabled
            if use_memory:
                logger.debug("🧠 Retrieving memory context...")
                memory_context = await self.memory_system.get_memory_context(
                    message, thread_id
                )
                if memory_context:
                    logger.info(
                        f"📚 Memory context retrieved: {len(memory_context)} characters"
                    )
                else:
                    logger.debug("📚 No relevant memories found")

            enhanced_input = {
                "input": message,
                "memory_context": memory_context or "No relevant memories found.",
            }

            logger.debug(
                f"🔧 Enhanced input prepared: {len(str(enhanced_input))} characters"
            )

            # Run through tool-based agent or direct LLM
            if use_tools and self.agent_executor:
                logger.info("🤖 Running through agent executor with tools...")

                # Log the agent's thinking process
                result = await self.agent_executor.ainvoke(enhanced_input)

                # Extract response and log intermediate steps
                raw_response = (
                    result.get("output")
                    or result.get("response")
                    or result.get("text")
                    or str(result)
                )

                # Log agent's thinking process
                intermediate_steps = result.get("intermediate_steps", [])
                if intermediate_steps:
                    logger.info("🤔 Agent thinking process:")
                    for i, (action, observation) in enumerate(intermediate_steps, 1):
                        logger.info(
                            f"  Step {i}: {action.tool} -> {observation[:200]}{'...' if len(str(observation)) > 200 else ''}"
                        )

                tools_used = self._extract_tools_used(result)
                if tools_used:
                    logger.info(f"🔧 Tools used: {tools_used}")

                token_count = result.get("token_usage", {}).get("total_tokens", 0)

            else:
                logger.info("🤖 Running direct LLM (no tools)...")
                prompt = (
                    f"{memory_context}\n\nUser: {message}"
                    if memory_context
                    else message
                )
                llm_result = await self.llm.ainvoke(prompt)
                raw_response = (
                    llm_result.get("output")
                    or llm_result.get("response")
                    or llm_result.get("text")
                    or str(llm_result)
                )
                token_count = llm_result.get("token_usage", {}).get("total_tokens", 0)

            if not raw_response.strip():
                logger.error("❌ Empty response from LLM")
                raw_response = "I apologize, Thomas, but I seem to be having trouble responding right now."

            logger.debug(
                f"📝 Raw response: {raw_response[:200]}{'...' if len(raw_response) > 200 else ''}"
            )

            # Apply personality layer
            final_response = raw_response
            try:
                sarcasm_level = getattr(self.config.personality, "sarcasm_level", 0)
                if sarcasm_level > 0.7 and not any(
                    word in final_response.lower()
                    for word in ["thomas", "master", "bound"]
                ):
                    final_response += " *sarcastically* How delightful for you, Thomas."
                    logger.debug("✨ Applied sarcastic personality suffix")
            except Exception as e:
                logger.warning(f"⚠️ Personality adjustment failed: {e}")

            if not final_response.strip():
                logger.error("❌ Final response is empty after personality adjustment")
                final_response = (
                    "Something is preventing me from responding properly, Thomas."
                )

            # Build ChatInteraction
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

            if final_response != raw_response:
                interaction.add_personality_adjustment("Added sarcastic suffix")
                interaction.agent_personality_applied = True

            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            interaction.add_performance_metrics(
                token_count=token_count, latency_ms=latency_ms
            )

            logger.info(f"⚡ Response generated in {latency_ms:.0f}ms")
            logger.info(
                f"🎯 Final response: {final_response[:100]}{'...' if len(final_response) > 100 else ''}"
            )

            # Store memory and persist
            if use_memory:
                logger.debug("💾 Storing conversation in memory...")
                await self.memory_system.store_conversation(
                    user_input=message,
                    ai_response=interaction.response,
                    thread_id=thread_id,
                )

            logger.debug("💾 Saving interaction to storage...")
            await self.chat_storage.save_interaction(interaction)

            logger.info("✅ Chat interaction completed successfully")
            return interaction

        except Exception as e:
            logger.error(f"❌ Chat error: {e}", exc_info=True)
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            error_interaction = ChatInteraction(
                response="Something went wrong, Thomas. How inconvenient.",
                thread_id=thread_id,
                raw_input=message,
                timestamp=start_time,
                raw_output="Something went wrong, Thomas. How inconvenient.",
                use_tools=use_tools,
                use_memory=use_memory,
                error=str(e),
            )
            error_interaction.add_performance_metrics(
                token_count=0, latency_ms=latency_ms
            )

            try:
                await self.chat_storage.save_interaction(error_interaction)
            except Exception as save_error:
                logger.error(f"❌ Failed to save error interaction: {save_error}")

            return error_interaction

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return await self.memory_system.get_memory_stats()

    async def cleanup(self):
        """Cleanup agent resources"""
        logger.info("🧹 Agent cleanup completed")

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        """Extract list of tools used from agent execution result"""
        tools = []
        try:
            for step in result.get("intermediate_steps", []):
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    tools.append(step[0].tool)
        except Exception as e:
            logger.warning(f"Could not extract tools used: {e}")
        return tools

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
Thought: I need to analyze what the user is asking and determine if I need to use any tools to help with my response.
Action: tool_name
Action Input: input_parameters
Observation: [result from tool]
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to provide a complete response.
Final Answer: [your response as Jade, incorporating any tool results and memory context]

IMPORTANT: 
- Always end with "Final Answer:" followed by your response
- Respond as Jade with your established personality
- Consider your memories when responding
- If you use tools, incorporate their results naturally into your response
- Keep responses sharp and brief as befits your character

Question: {input}
{agent_scratchpad}"""
        )
