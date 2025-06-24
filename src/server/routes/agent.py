# src/server/routes/agent.py - Updated with Prompt Engineering Integration

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
from src.shared.react_step import ReActStep


from src.prompts.orchestrator import PromptOrchestrator
from src.prompts.models import PromptTechnique, ExecutionContext
from src.core.registry import ServiceRegistry

logger = logging.getLogger(__name__)

DEFAULT_THREAD_ID = "default"


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

        # NEW: Initialize prompt orchestrator
        self.prompt_orchestrator: Optional[PromptOrchestrator] = None
        self.enable_advanced_prompting = getattr(
            config, "enable_advanced_prompting", False
        )

    def _create_callback_manager(self):
        from langchain.callbacks.manager import CallbackManager

        return CallbackManager([])

    async def initialize(self):
        tools = self.tool_registry.get_all_tools()
        logger.info("🔍 Validating ReAct prompt from config...")
        if not ReActPromptValidator.validate_prompt(self.config):
            for suggestion in ReActPromptValidator.suggest_fixes(self.config):
                logger.error(f"💡 {suggestion}")
            raise ValueError("Invalid ReAct prompt configuration.")

        prompt = PromptTemplate(
            input_variables=self.config.prompts.variables + ["tool_used", "step_count"],
            template=self.config.prompts.base_prompt.strip(),
        )

        callback_manager = self._create_callback_manager()
        agent = create_react_agent(self.llm, tools, prompt)

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            callback_manager=callback_manager,
            verbose=True,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="force",
        )

        # NEW: Initialize prompt orchestrator
        try:
            self.prompt_orchestrator = ServiceRegistry.get("prompt_orchestrator")
            logger.info("✅ Prompt orchestrator connected to agent")
        except Exception as e:
            logger.warning(f"⚠️ Prompt orchestrator not available: {e}")
            self.enable_advanced_prompting = False

        logger.info(f"🪠 Tools registered: {[tool.name for tool in tools]}")

    # NEW: Method to analyze if advanced prompting is needed
    def _should_use_advanced_prompting(self, message: str) -> Optional[PromptTechnique]:
        """Analyze message to determine if advanced prompting would be beneficial"""
        if not self.enable_advanced_prompting or not self.prompt_orchestrator:
            return None

        message_lower = message.lower()

        # Detect mathematical/calculation problems
        math_keywords = [
            "calculate",
            "solve",
            "equation",
            "math",
            "arithmetic",
            "compute",
            "what is",
            "how much",
        ]
        if any(keyword in message_lower for keyword in math_keywords):
            # Check for multi-step problems
            if any(
                indicator in message_lower
                for indicator in ["step", "process", "how to", "explain"]
            ):
                logger.info("🧠 Detected complex math problem, using chain-of-thought")
                return PromptTechnique.CHAIN_OF_THOUGHT

        # Detect reasoning/analysis tasks
        reasoning_keywords = [
            "analyze",
            "compare",
            "evaluate",
            "assess",
            "why",
            "explain",
            "reason",
        ]
        if any(keyword in message_lower for keyword in reasoning_keywords):
            # For complex analysis, use self-consistency
            if len(message.split()) > 20:  # Longer queries
                logger.info("🧠 Detected complex analysis task, using self-consistency")
                return PromptTechnique.SELF_CONSISTENCY

        # Detect requests for structured responses
        structure_keywords = ["format", "template", "example", "style", "pattern"]
        if any(keyword in message_lower for keyword in structure_keywords):
            logger.info("🧠 Detected request for structured response, using few-shot")
            return PromptTechnique.FEW_SHOT

        return None

    # NEW: Method to execute advanced prompting
    async def _execute_advanced_prompting(
        self,
        technique: PromptTechnique,
        message: str,
        thread_id: str,
        memory_context: str,
    ) -> AgentResult:
        """Execute advanced prompting technique"""
        start_time = datetime.utcnow()

        try:
            logger.info(f"🧠 Using advanced prompting: {technique.value}")

            # Execute the prompt technique
            result = await self.prompt_orchestrator.execute_technique(
                technique=technique,
                query=message,
                thread_id=thread_id,
                llm=self.llm,
                memory_system=self.memory_system,
                use_memory=True,
            )

            if result.execution_successful:
                # Convert to AgentResult format
                agent_result = AgentResult(
                    raw_input=message,
                    raw_output=result.generated_content,
                    final_response=result.generated_content,
                    tools_used=[],  # Advanced prompting doesn't use tools
                    token_count=result.token_count or 0,
                    memory_context=result.memory_context,
                    intermediate_steps=result.intermediate_steps,
                    react_steps=[],  # Advanced prompting has different step format
                    thread_id=thread_id,
                    timestamp=start_time,
                )

                logger.info(f"✅ Advanced prompting successful with {technique.value}")
                return agent_result
            else:
                logger.warning(f"⚠️ Advanced prompting failed: {result.error_message}")
                # Fall back to normal processing
                return None

        except Exception as e:
            logger.error(f"❌ Advanced prompting error: {e}")
            # Fall back to normal processing
            return None

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        try:
            return [
                step[0].tool
                for step in result.get("intermediate_steps", [])
                if len(step) >= 2 and hasattr(step[0], "tool")
            ]
        except Exception as e:
            logger.warning(f"❌ Could not extract tools used: {e}")
            return []

    def _format_prompt(
        self,
        message: str,
        memory_context: str,
        tools: List,
        tool_used: str,
        step_count: int,
    ) -> str:
        return self.config.prompts.base_prompt.format(
            input=message,
            agent_scratchpad="",
            memory_context=memory_context,
            tools="\n".join(f"{tool.name}: {tool.description}" for tool in tools),
            tool_names=", ".join(tool.name for tool in tools),
            step_count=step_count,
            tool_used=tool_used,
        )

    def extract_final_answer(self, output: str) -> Optional[str]:
        matches = re.findall(r"Final Answer:\s*(.+)", str(output), flags=re.IGNORECASE)
        return matches[-1].strip() if matches else None

    def _concat_thoughts(self, intermediate_steps: List[Any]) -> str:
        thoughts = []
        for step in intermediate_steps:
            if hasattr(step[0], "log"):
                match = re.search(r"Thought:\s*(.*)", step[0].log)
                if match:
                    thoughts.append(match.group(1).strip())
        return " ".join(thoughts)

    async def chat(
        self, message: str, thread_id: str = DEFAULT_THREAD_ID, use_tools: bool = True
    ) -> AgentResult:
        start_time = datetime.utcnow()
        logger.info(
            f"💬 Processing: '{message[:100]}{'...' if len(message) > 100 else ''}'"
        )

        memory_context = await self.memory_builder.build_context(message, thread_id)

        # NEW: Check if advanced prompting should be used
        advanced_technique = self._should_use_advanced_prompting(message)
        if advanced_technique:
            advanced_result = await self._execute_advanced_prompting(
                advanced_technique, message, thread_id, memory_context
            )
            if advanced_result:
                # Save interaction and return advanced result
                await self._save_interaction_from_result(
                    advanced_result, use_tools, True
                )
                return advanced_result
            # If advanced prompting fails, continue with normal processing
            logger.info("🔄 Falling back to normal agent processing")

        # Continue with existing normal processing...
        tools = self.tool_registry.get_all_tools()
        raw_output = ""
        final_response: Optional[str] = None
        tools_used: List[str] = []
        token_count = 0
        intermediate_steps: List[Any] = []

        try:
            if use_tools:
                if not self.agent_executor:
                    raise RuntimeError(
                        "AgentExecutor not initialized. Did you forget to call initialize()?"
                    )

                logger.info("🤖 Invoking agent executor with tools...")
                agent_input = {
                    "input": message,
                    "agent_scratchpad": "",
                    "memory_context": memory_context,
                    "tools": "\n".join(
                        f"{tool.name}: {tool.description}" for tool in tools
                    ),
                    "tool_names": ", ".join(tool.name for tool in tools),
                    "step_count": 0,
                    "tool_used": "false",
                }

                result = await self.agent_executor.ainvoke(agent_input)
                intermediate_steps = result.get("intermediate_steps", [])
                step_count = len(intermediate_steps)
                tools_used = self._extract_tools_used(result)
                raw_output = result.get("output") or str(result)
                final_response = self.extract_final_answer(raw_output)

                if not final_response and step_count >= self.config.max_iterations:
                    logger.warning("⚠️ Reached max steps without final answer.")
                    summarized_thoughts = self._concat_thoughts(intermediate_steps)
                    logger.debug(f"🧠 Thought Summary for Retry: {summarized_thoughts}")
                    prompt = self._format_prompt(
                        message,
                        memory_context
                        + f"\nSummarized Thoughts: {summarized_thoughts}",
                        tools,
                        tool_used="false",
                        step_count=step_count,
                    )
                    raw_output = await self.llm.ainvoke(prompt)
                    final_response = self.extract_final_answer(str(raw_output))

                token_count = result.get("token_usage", {}).get("total_tokens", 0)

            else:
                logger.info("💬 Invoking LLM without tools...")
                step_count = 0
                prompt = self._format_prompt(
                    message,
                    memory_context,
                    tools,
                    tool_used="false",
                    step_count=step_count,
                )
                raw_output = await self.llm.ainvoke(prompt)
                final_response = self.extract_final_answer(str(raw_output))

        except Exception as e:
            logger.exception("❌ Agent or LLM invocation failed")
            raise

        react_steps = (
            ReActStep.extract_react_steps(intermediate_steps)
            or ReActStep.extract_from_raw_output(raw_output)
            or [
                ReActStep(
                    thought="Processing user request...",
                    action="",
                    action_input="",
                    observation="",
                    final_answer=final_response or "",
                )
            ]
        )

        agent_result = AgentResult(
            raw_input=message,
            raw_output=raw_output,
            final_response=final_response or "",
            tools_used=tools_used,
            token_count=token_count,
            memory_context=memory_context,
            intermediate_steps=intermediate_steps,
            react_steps=react_steps,
            thread_id=thread_id,
            timestamp=start_time,
        )

        # Save interaction
        await self._save_interaction_from_result(agent_result, use_tools, False)

        return agent_result

    # NEW: Helper method to save interactions (reduces code duplication)
    async def _save_interaction_from_result(
        self, agent_result: AgentResult, use_tools: bool, used_advanced_prompting: bool
    ):
        """Save interaction from AgentResult"""
        interaction = ChatInteraction(
            thread_id=agent_result.thread_id,
            timestamp=agent_result.timestamp,
            raw_input=agent_result.raw_input,
            raw_output=agent_result.raw_output,
            response=agent_result.final_response,
            tools_used=agent_result.tools_used,
            memory_context_used=bool(agent_result.memory_context.strip()),
            memory_context=agent_result.memory_context,
            use_tools=use_tools,
            use_memory=True,
            token_count=agent_result.token_count,
            response_time_ms=(
                datetime.utcnow() - agent_result.timestamp
            ).total_seconds()
            * 1000,
        )

        # Add metadata about advanced prompting
        if used_advanced_prompting:
            interaction.metadata["advanced_prompting"] = True
            interaction.metadata["prompting_technique"] = "advanced"

        # Process through output adapters
        if self.output_adapter_manager:
            try:
                processed = await self.output_adapter_manager.process_interaction(
                    interaction
                )
                if processed.metadata.get("tts_enabled"):
                    logger.info("🎵 TTS audio generated")
            except Exception as e:
                logger.error(f"❌ Output adapter failed: {e}")

        # Save to memory
        try:
            await self.memory_system.save_interaction(interaction)
        except Exception as e:
            logger.error(f"❌ Failed to save interaction: {e}")

