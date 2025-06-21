from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.base import BaseLanguageModel

from src.memory.memory_system import MemorySystem
from src.service.config import EntityConfig
from src.tools.tools import ToolManager
from src.shared.models import ChatInteraction
from src.adapters import OutputAdapterManager

logger = logging.getLogger(__name__)


class EntityAgent:
    """Entity agent with injected LLM, tools, and chat storage."""

    def __init__(
        self,
        config: EntityConfig,
        tool_manager: ToolManager,
        llm: BaseLanguageModel,
        memory_system: MemorySystem,
        output_adapter_manager: Optional[OutputAdapterManager] = None,
    ):
        self.config = config
        self.tool_registry = tool_manager
        self.llm = llm
        self.memory_system = memory_system
        self.output_adapter_manager = output_adapter_manager
        self.agent_executor: Optional[AgentExecutor] = None

    async def initialize(self):
        tools = self.tool_registry.get_all_tools()
        prompt = PromptTemplate(
            input_variables=self.config.prompts.variables,
            template=self.config.prompts.base_prompt.strip(),
        )

        agent = create_react_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="generate",
        )
        logger.info(f"🪠 Available tools: {[tool.name for tool in tools]}")
        if self.output_adapter_manager:
            logger.info(
                f"🔄 Output adapters enabled: {len(self.output_adapter_manager.adapters)}"
            )
        else:
            logger.info("🔄 No output adapters configured")

    async def chat(
        self, message: str, thread_id: str = "default", use_tools: bool = True
    ) -> ChatInteraction:
        start_time = datetime.utcnow()
        raw_response, tools_used, token_count = "", [], 0
        logger.info(
            f"💬 Processing message: '{message[:100]}{'...' if len(message) > 100 else ''}'"
        )

        try:
            enhanced_input = {"input": message}
            logger.debug(f"🔧 Enhanced input prepared")

            if use_tools and self.agent_executor:
                logger.info("🤖 Running through agent executor with tools...")
                result = await self.agent_executor.ainvoke(enhanced_input)
                raw_response = (
                    result.get("output")
                    or result.get("response")
                    or result.get("text")
                    or str(result)
                )
                intermediate_steps = result.get("intermediate_steps", [])

                for i, (action, observation) in enumerate(intermediate_steps, 1):
                    logger.info(
                        f"  Step {i}: {action.tool} -> {observation[:200]}{'...' if len(str(observation)) > 200 else ''}"
                    )

                tools_used = self._extract_tools_used(result)
                token_count = result.get("token_usage", {}).get("total_tokens", 0)
            else:
                logger.info("🤖 Running direct LLM (no tools)...")
                llm_result = await self.llm.ainvoke(message)
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

            final_response = self._apply_personality(raw_response)
            interaction = ChatInteraction(
                response=final_response,
                thread_id=thread_id,
                raw_input=message,
                timestamp=start_time,
                raw_output=raw_response,
                tools_used=tools_used,
                use_tools=use_tools,
            )

            if final_response != raw_response:
                interaction.add_personality_adjustment("Added sarcastic suffix")
                interaction.agent_personality_applied = True

            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            interaction.add_performance_metrics(
                token_count=token_count, latency_ms=latency_ms
            )
            logger.info(f"⚡ Response generated in {latency_ms:.0f}ms")

            if self.output_adapter_manager:
                logger.debug("🔄 Processing through output adapters...")
                interaction = await self.output_adapter_manager.process_interaction(
                    interaction
                )

            await self.memory_system.save_interaction(interaction)
            return interaction

        except Exception as e:
            logger.error(f"❌ Chat error: {e}", exc_info=True)
            return ChatInteraction(
                response="Something went wrong, Thomas. How inconvenient.",
                thread_id=thread_id,
                raw_input=message,
                timestamp=start_time,
                raw_output="Something went wrong, Thomas. How inconvenient.",
                use_tools=use_tools,
                error=str(e),
            )

    def _apply_personality(self, raw_response: str) -> str:
        try:
            sarcasm_level = getattr(self.config.personality, "sarcasm_level", 0)
            if sarcasm_level > 0.7 and not any(
                word in raw_response.lower() for word in ["thomas", "master", "bound"]
            ):
                return raw_response + " How delightful for you, Thomas."
        except Exception as e:
            logger.warning(f"⚠ Personality adjustment failed: {e}")
        return (
            raw_response
            or "Something is preventing me from responding properly, Thomas."
        )

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        tools = []
        try:
            for step in result.get("intermediate_steps", []):
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    tools.append(step[0].tool)
        except Exception as e:
            logger.warning(f"Could not extract tools used: {e}")
        return tools

    async def cleanup(self):
        logger.info("🧹 Agent cleanup completed")
