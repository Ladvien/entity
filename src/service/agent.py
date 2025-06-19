from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.base import BaseLanguageModel

from src.service.config import EntityConfig
from src.storage import ChatStorage
from src.tools.memory import VectorMemorySystem
from src.tools.tools import ToolRegistry

logger = logging.getLogger(__name__)


class EntityAgent:
    """Entity agent with injected LLM and vector memory"""

    def __init__(
        self,
        config: EntityConfig,
        tool_registry: ToolRegistry,
        storage: ChatStorage,
        memory_system: VectorMemorySystem,
        llm: BaseLanguageModel,  # Injected dependency
    ):
        self.config = config
        self.tool_registry = tool_registry
        self.storage = storage
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
    ) -> Dict[str, Any]:
        start_time = datetime.utcnow()

        try:
            memory_context = ""
            if use_memory:
                memory_context = await self.memory_system.get_memory_context(
                    message, thread_id
                )

            enhanced_input = {
                "input": message,
                "memory_context": memory_context or "No relevant memories found.",
            }

            if use_tools and self.agent_executor:
                result = await self.agent_executor.ainvoke(enhanced_input)

                # Log intermediate steps
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

                # 🛡️ Defensive handling for raw string or dict
                if isinstance(result, dict):
                    response = (
                        result.get("output")
                        or result.get("response")
                        or result.get("text")
                        or str(result)
                    )
                    tools_used = self._extract_tools_used(result)
                else:
                    response = str(result)
                    tools_used = []

            else:
                prompt = (
                    f"{memory_context}\n\nUser: {message}"
                    if memory_context
                    else message
                )

                llm_result = await self.llm.ainvoke(prompt)

                # 🛡️ Normalize LLM response to string
                if isinstance(llm_result, dict):
                    response = (
                        llm_result.get("output")
                        or llm_result.get("response")
                        or llm_result.get("text")
                        or str(llm_result)
                    )
                else:
                    response = str(llm_result)

                tools_used = []

            response = self._adjust_personality(response)

            if use_memory:
                await self.memory_system.store_conversation(
                    user_input=message,
                    ai_response=response,
                    thread_id=thread_id,
                )

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

    async def get_memory_stats(self) -> Dict[str, Any]:
        return await self.memory_system.get_memory_stats()

    async def cleanup(self):
        logger.info("Agent cleanup completed")

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        return [
            step[0].tool
            for step in result.get("intermediate_steps", [])
            if len(step) >= 2 and hasattr(step[0], "tool")
        ]

    def _adjust_personality(self, response: str) -> str:
        # Only modify if sarcasm is high and trigger words missing
        try:
            sarcasm_level = getattr(self.config.personality, "sarcasm_level", 0)
            if sarcasm_level > 0.7 and not any(
                keyword in response.lower() for keyword in ["thomas", "master", "bound"]
            ):
                response += " *sarcastically* How delightful for you, Thomas."
        except Exception as e:
            logger.warning(f"Personality tweak failed: {e}")
        return response

    def _build_prompt_template(self) -> str:
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
