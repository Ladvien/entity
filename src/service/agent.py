# entity_service/agent.py
"""
Entity Agent with PostgreSQL Memory Integration
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent

from entity_service.config import AgentConfig
from entity_service.tools import ToolRegistry
from entity_service.storage import ChatStorage
from entity_service.memory import VectorMemorySystem

logger = logging.getLogger(__name__)


class EntityAgent:
    """Entity agent with vector memory"""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: ToolRegistry,
        storage: ChatStorage,
        memory_system: VectorMemorySystem,
    ):
        self.config = config
        self.tool_registry = tool_registry
        self.storage = storage
        self.memory_system = memory_system
        self.llm = None
        self.agent_executor = None

    async def initialize(self):
        """Initialize the agent"""
        # Create LLM
        self.llm = OllamaLLM(
            base_url=self.config.base_url,
            model=self.config.model,
            temperature=self.config.temperature,
        )

        # Create prompt template with memory context
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

        # Get tools
        tools = self.tool_registry.get_all_tools()

        # Create agent
        agent = create_react_agent(self.llm, tools, prompt)

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=3,
            handle_parsing_errors=True,
        )

        logger.info(f"✅ Agent initialized with {len(tools)} tools and vector memory")

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        use_tools: bool = True,
        use_memory: bool = True,
    ) -> Dict[str, Any]:
        """Process a chat message with memory context"""
        start_time = datetime.utcnow()

        try:
            # Get memory context if enabled
            memory_context = ""
            if use_memory:
                memory_context = await self.memory_system.get_memory_context(
                    message, thread_id
                )
                if memory_context:
                    logger.info(f"📚 Retrieved memory context for query")

            # Build enhanced input with memory
            enhanced_input = {
                "input": message,
                "memory_context": memory_context or "No relevant memories found.",
            }

            # Execute agent
            if use_tools and self.agent_executor:
                result = await self.agent_executor.ainvoke(enhanced_input)
                response = result["output"]
                tools_used = self._extract_tools_used(result)
            else:
                # Direct LLM call without tools but with memory
                prompt = (
                    f"{memory_context}\n\nUser: {message}"
                    if memory_context
                    else message
                )
                response = await self.llm.ainvoke(prompt)
                tools_used = []

            # Apply personality adjustments
            response = self._adjust_personality(response)

            # Store conversation in vector memory
            if use_memory:
                await self.memory_system.store_conversation(
                    user_input=message, ai_response=response, thread_id=thread_id
                )

            # Save raw chat history
            await self.storage.save_interaction(
                thread_id=thread_id,
                user_input=message,
                agent_output=response,
                metadata={
                    "timestamp": start_time,
                    "tools_used": tools_used,
                    "use_tools": use_tools,
                    "use_memory": use_memory,
                    "had_memory_context": bool(memory_context),
                },
            )

            return {
                "response": response,
                "thread_id": thread_id,
                "timestamp": start_time,
                "tools_used": tools_used,
                "raw_input": message,
                "raw_output": response,
                "memory_context_used": bool(memory_context),
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            error_response = "Something went wrong, Thomas. How inconvenient."

            return {
                "response": error_response,
                "thread_id": thread_id,
                "timestamp": start_time,
                "tools_used": [],
                "raw_input": message,
                "raw_output": error_response,
                "error": str(e),
            }

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Agent cleanup completed")

    def _build_prompt_template(self) -> str:
        """Build the prompt template with memory context"""
        base_prompt = (
            self.config.personality.base_prompt
            or f"""
You are {self.config.personality.name}, an entity with specific traits and memories.
"""
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

    def _adjust_personality(self, response: str) -> str:
        """Apply personality adjustments"""
        traits = self.config.personality.traits

        # Add personality suffixes based on traits
        if traits.get("sarcasm", 0) > 0.7 and not any(
            keyword in response.lower() for keyword in ["thomas", "master", "bound"]
        ):
            response += " *sarcastically* How delightful for you, Thomas."

        return response

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        """Extract which tools were used"""
        tools_used = []
        for step in result.get("intermediate_steps", []):
            if len(step) >= 2 and hasattr(step[0], "tool"):
                tools_used.append(step[0].tool)
        return tools_used

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return await self.memory_system.get_memory_stats()
