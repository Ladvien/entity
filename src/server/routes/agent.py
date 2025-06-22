# src/server/routes/agent.py - UPDATED WITH OUTPUT ADAPTER INTEGRATION

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import re
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.base import BaseLanguageModel

from src.memory.memory_system import MemorySystem
from src.plugins.registry import ToolManager
from src.core.config import EntityConfig
from src.service.react_validator import ReActPromptValidator
from src.shared.agent_result import AgentResult
from src.shared.models import ChatInteraction
from src.adapters import OutputAdapterManager

logger = logging.getLogger(__name__)


class MemoryContextBuilder:
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system

    async def build_context(self, message: str, thread_id: str) -> str:
        try:
            memories = await self.memory_system.search_memory(message, thread_id, k=5)
            memory_context = "\n".join(doc.page_content for doc in memories)
            if not memory_context.strip():
                logger.info("🔍 No vector memory found, falling back to deep search.")
                deep_hits = await self.memory_system.deep_search_memory(
                    message, thread_id, k=5
                )
                memory_context = "\n".join(i.response for i in deep_hits)
            return memory_context
        except Exception as e:
            logger.warning(f"⚠️ Memory search failed: {e}")
            return ""


class EntityAgent:
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
        self.memory_builder = MemoryContextBuilder(memory_system)

    async def initialize(self):
        tools = self.tool_registry.get_all_tools()

        # Validate the prompt from config
        logger.info("🔍 Validating ReAct prompt from config...")
        if not ReActPromptValidator.validate_prompt(self.config):
            logger.error("❌ Prompt validation failed!")
            suggestions = ReActPromptValidator.suggest_fixes(self.config)
            for suggestion in suggestions:
                logger.error(f"💡 Suggestion: {suggestion}")
            raise ValueError(
                "Invalid ReAct prompt configuration. Check logs for details."
            )

        # Use prompt directly from config
        prompt = PromptTemplate(
            input_variables=self.config.prompts.variables,
            template=self.config.prompts.base_prompt.strip(),
        )

        logger.debug(f"🛠️ Initializing ReAct agent with {len(tools)} tools")
        logger.info(f"🎯 Using ReAct agent (Ollama compatible)")

        agent = create_react_agent(self.llm, tools, prompt)

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="force",
            callback_manager=self._create_callback_manager(),
        )

        logger.info(f"🪠 Available tools: {[tool.name for tool in tools]}")
        logger.info(f"✅ ReAct agent executor initialized")

        # Log output adapter status
        if self.output_adapter_manager and self.output_adapter_manager.adapters:
            adapter_names = [
                adapter.__class__.__name__
                for adapter in self.output_adapter_manager.adapters
            ]
            logger.info(f"🔌 Output adapters enabled: {', '.join(adapter_names)}")
        else:
            logger.info("🔌 No output adapters configured")

    def _create_callback_manager(self):
        """Create callback manager to handle tool usage limits"""
        from langchain.callbacks.base import BaseCallbackHandler

        class ToolLimitCallback(BaseCallbackHandler):
            def __init__(self):
                self.tool_usage = {}
                self.max_per_tool = 2

            def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
                tool_name = serialized.get("name", "unknown")
                self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1

                if self.tool_usage[tool_name] > self.max_per_tool:
                    logger.warning(
                        f"🛑 Tool '{tool_name}' used {self.tool_usage[tool_name]} times, encouraging final answer"
                    )

            def on_tool_end(self, output: str, **kwargs):
                # Check if we should force a conclusion
                total_calls = sum(self.tool_usage.values())
                if total_calls >= 8:  # After 8 total tool calls, force conclusion
                    logger.warning("🛑 Too many tool calls, should conclude soon")

        from langchain.callbacks.manager import CallbackManager

        return CallbackManager([ToolLimitCallback()])

    async def chat(
        self, message: str, thread_id: str = "default", use_tools: bool = True
    ) -> AgentResult:
        start_time = datetime.utcnow()
        logger.info(
            f"💬 Processing message: '{message[:100]}{'...' if len(message) > 100 else ''}'"
        )

        memory_context = await self.memory_builder.build_context(message, thread_id)

        # Build input variables based on what the config prompt expects
        input_vars = {
            "input": message,
            "agent_scratchpad": "",  # This gets filled by the agent
        }

        # Add tools information if expected by prompt
        tools = self.tool_registry.get_all_tools()
        if "tools" in self.config.prompts.variables:
            input_vars["tools"] = "\n".join(
                f"{tool.name}: {tool.description}" for tool in tools
            )

        if "tool_names" in self.config.prompts.variables:
            input_vars["tool_names"] = ", ".join(tool.name for tool in tools)

        # Add memory context if expected by prompt
        if "memory_context" in self.config.prompts.variables:
            input_vars["memory_context"] = memory_context if memory_context else ""

        raw_output, final_response, tools_used, token_count, intermediate_steps = (
            "",
            "",
            [],
            0,
            [],
        )

        if use_tools and self.agent_executor:
            logger.info("🤖 Running through ReAct agent executor with tools...")

            try:
                input_vars["step_count"] = len(intermediate_steps)
                result = await self.agent_executor.ainvoke(input_vars)

                # Debug: Log what we actually get back
                logger.debug(f"🔍 Agent result keys: {list(result.keys())}")
                logger.debug(
                    f"🔍 Intermediate steps type: {type(result.get('intermediate_steps', []))}"
                )
                logger.debug(
                    f"🔍 Intermediate steps count: {len(result.get('intermediate_steps', []))}"
                )

                raw_output = (
                    result.get("output")
                    or result.get("response")
                    or result.get("text")
                    or str(result)
                )
                final_response = self.extract_final_answer(raw_output)
                tools_used = self._extract_tools_used(result)
                token_count = result.get("token_usage", {}).get("total_tokens", 0)
                intermediate_steps = result.get("intermediate_steps", [])

                if intermediate_steps:
                    logger.info(f"🎯 Got {len(intermediate_steps)} intermediate steps")
                else:
                    logger.warning("⚠️ No intermediate steps found in agent result")

            except ValueError as e:
                if "early_stopping_method" in str(e):
                    logger.error(f"❌ Agent configuration error: {e}")
                    raw_output = f"Configuration Error: {str(e)}"
                    final_response = "There's a configuration issue with my reasoning system. Let me respond directly."
                    # Try direct response without agent
                    try:
                        formatted_prompt = self.config.prompts.base_prompt.format(
                            **input_vars
                        )
                        direct_response = await self.llm.ainvoke(formatted_prompt)
                        final_response = self.extract_final_answer(str(direct_response))
                    except Exception as direct_e:
                        logger.error(f"❌ Direct LLM also failed: {direct_e}")
                        final_response = "Hey yourself. What do you want?"
                else:
                    logger.error(f"❌ Agent execution failed: {e}", exc_info=True)
                    raw_output = f"Error: {str(e)}"
                    final_response = (
                        "I encountered an error while processing your request."
                    )

            except Exception as e:
                logger.error(f"❌ Agent execution failed: {e}", exc_info=True)
                raw_output = f"Error: {str(e)}"
                final_response = "I encountered an error while processing your request."

        else:
            logger.info("🤖 Running without tools (direct LLM)")
            try:
                # For direct LLM, just format the base prompt with available variables
                formatted_prompt = self.config.prompts.base_prompt.format(**input_vars)
                raw_output = await self.llm.ainvoke(formatted_prompt)
                final_response = self.extract_final_answer(str(raw_output))
            except Exception as e:
                logger.error(f"❌ LLM invocation failed: {e}")
                raw_output = f"Error: {str(e)}"
                final_response = "I encountered an error while processing your request."

        if not final_response.strip():
            logger.error("❌ Empty response from LLM")
            final_response = "Hey yourself. What do you want from me?"

        # Extract ReAct steps
        from src.shared.react_step import ReActStep

        react_steps = []

        # Method 1: Try to extract from proper intermediate steps
        if intermediate_steps:
            logger.info(
                f"🔄 Extracting ReAct steps from {len(intermediate_steps)} intermediate steps"
            )
            react_steps = ReActStep.extract_react_steps(intermediate_steps)

        # Method 2: Fallback to parsing raw output if no proper steps
        if not react_steps and raw_output:
            logger.info("🔄 Fallback: Extracting ReAct steps from raw output")
            react_steps = ReActStep.extract_from_raw_output(raw_output)

        # Method 3: Emergency fallback - create a single step from the whole response
        if not react_steps:
            logger.warning("⚠️ Creating emergency fallback step")
            react_steps = [
                ReActStep(
                    thought="Processing user request...",
                    action="",
                    action_input="",
                    observation="",
                    final_answer=final_response,
                )
            ]

        logger.info(f"✅ Final ReAct steps count: {len(react_steps)}")

        # Create the AgentResult
        agent_result = AgentResult(
            raw_input=message,
            raw_output=raw_output,
            final_response=final_response,
            tools_used=tools_used,
            token_count=token_count,
            memory_context=memory_context,
            intermediate_steps=intermediate_steps,
            react_steps=react_steps,
            thread_id=thread_id,
            timestamp=start_time,
        )

        # Create ChatInteraction for storage and adapter processing
        interaction = ChatInteraction(
            thread_id=thread_id,
            timestamp=start_time,
            raw_input=message,
            raw_output=raw_output,
            response=final_response,
            tools_used=tools_used,
            memory_context_used=bool(memory_context.strip()),
            memory_context=memory_context,
            use_tools=use_tools,
            use_memory=True,
            token_count=token_count,
            response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
        )

        # Process through output adapters (including TTS)
        if self.output_adapter_manager:
            try:
                logger.info("🔌 Processing through output adapters...")
                processed_interaction = (
                    await self.output_adapter_manager.process_interaction(interaction)
                )

                # Update agent result with any adapter-added metadata
                if processed_interaction.metadata:
                    logger.info(
                        f"🔌 Adapter metadata: {list(processed_interaction.metadata.keys())}"
                    )

                    # Add TTS metadata to agent result if present
                    if processed_interaction.metadata.get("tts_enabled"):
                        logger.info("🎵 TTS audio generated successfully")
                        # You could add audio metadata to the agent result here if needed

            except Exception as e:
                logger.error(f"❌ Output adapter processing failed: {e}")
                # Continue anyway - adapters are not critical for basic functionality

        # Save to memory system
        try:
            await self.memory_system.save_interaction(interaction)
            logger.debug("💾 Interaction saved to memory")
        except Exception as e:
            logger.error(f"❌ Failed to save interaction to memory: {e}")

        return agent_result

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        tools = []
        try:
            for step in result.get("intermediate_steps", []):
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    tools.append(step[0].tool)
        except Exception as e:
            logger.warning(f"Could not extract tools used: {e}")
        return tools

    def extract_final_answer(self, output: str) -> str:
        # Handle both string and other types
        if not isinstance(output, str):
            output = str(output)

        match = re.search(
            r"Final Answer:\s*(.*)", output, flags=re.IGNORECASE | re.DOTALL
        )
        return match.group(1).strip() if match else output.strip()

    async def cleanup(self):
        # Close output adapters if we own them
        if self.output_adapter_manager:
            await self.output_adapter_manager.close_all()
        logger.info("🧹 Agent cleanup completed")
