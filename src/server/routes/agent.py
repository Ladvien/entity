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
        self._tool_limit_callback = None

    def _create_callback_manager(self):
        from langchain.callbacks.base import BaseCallbackHandler
        from langchain.callbacks.manager import CallbackManager

        class ToolLimitCallback(BaseCallbackHandler):
            def __init__(self, max_per_tool=2, max_total=5):
                self.tool_usage = {}
                self.max_per_tool = max_per_tool
                self.max_total = max_total
                self.tool_used = False
                self.tool_exhausted = False

            def should_stop(self) -> bool:
                return self.tool_exhausted

            def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
                tool_name = serialized.get("name", "unknown")
                self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1
                self.tool_used = True

                if self.tool_usage[tool_name] >= self.max_per_tool:
                    logger.debug(f"⚠️ Tool '{tool_name}' reached per-tool limit")

                if sum(self.tool_usage.values()) >= self.max_total:
                    self.tool_exhausted = True
                    logger.debug("🧯 Total tool use limit reached")

        self._tool_limit_callback = ToolLimitCallback()
        return CallbackManager([self._tool_limit_callback])

    async def initialize(self):
        tools = self.tool_registry.get_all_tools()
        logger.info("🔍 Validating ReAct prompt from config...")
        if not ReActPromptValidator.validate_prompt(self.config):
            for suggestion in ReActPromptValidator.suggest_fixes(self.config):
                logger.error(f"💡 {suggestion}")
            raise ValueError("Invalid ReAct prompt configuration.")

        prompt = PromptTemplate(
            input_variables=self.config.prompts.variables + ["tool_used"],
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

        logger.info(f"🪠 Tools registered: {[tool.name for tool in tools]}")

    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        tools = []
        try:
            for step in result.get("intermediate_steps", []):
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    tools.append(step[0].tool)
        except Exception as e:
            logger.warning(f"❌ Could not extract tools used: {e}")
        return tools

    def extract_final_answer(self, output: str) -> str:
        output = str(output)
        match = re.search(
            r"Final Answer:\s*(.*)", output, flags=re.IGNORECASE | re.DOTALL
        )
        return match.group(1).strip() if match else output.strip()

    async def chat(
        self, message: str, thread_id: str = "default", use_tools: bool = True
    ) -> AgentResult:
        start_time = datetime.utcnow()
        logger.info(
            f"💬 Processing: '{message[:100]}{'...' if len(message) > 100 else ''}'"
        )

        memory_context = await self.memory_builder.build_context(message, thread_id)
        tools = self.tool_registry.get_all_tools()

        input_vars = {
            "input": message,
            "agent_scratchpad": "",
            "memory_context": memory_context,
            "tools": "\n".join(f"{tool.name}: {tool.description}" for tool in tools),
            "tool_names": ", ".join(tool.name for tool in tools),
            "step_count": 0,
            "tool_used": "false",
        }

        raw_output = ""
        final_response = ""
        tools_used: List[str] = []
        token_count = 0
        intermediate_steps: List[Any] = []

        try:
            if use_tools and self.agent_executor:
                logger.info("🤖 Invoking agent executor with tools...")
                result = await self.agent_executor.ainvoke(input_vars)

                if self._tool_limit_callback and self._tool_limit_callback.tool_used:
                    input_vars["tool_used"] = "true"

                raw_output = result.get("output") or str(result)
                final_response = self.extract_final_answer(raw_output)

                if (
                    self._tool_limit_callback
                    and self._tool_limit_callback.tool_exhausted
                ):
                    raise RuntimeError(
                        "All tools exhausted before agent produced final answer."
                    )

                if "Agent stopped due to" in final_response:
                    raise RuntimeError(
                        f"Agent failed to reach a final answer: {final_response}"
                    )

                tools_used = self._extract_tools_used(result)
                token_count = result.get("token_usage", {}).get("total_tokens", 0)
                intermediate_steps = result.get("intermediate_steps", [])
            else:
                logger.info("💬 Invoking LLM without tools...")
                prompt = self.config.prompts.base_prompt.format(**input_vars)
                raw_output = await self.llm.ainvoke(prompt)
                final_response = self.extract_final_answer(str(raw_output))

        except Exception as e:
            logger.exception("❌ Agent or LLM invocation failed")
            raise

        from src.shared.react_step import ReActStep

        react_steps = (
            ReActStep.extract_react_steps(intermediate_steps)
            or ReActStep.extract_from_raw_output(raw_output)
            or [
                ReActStep(
                    thought="Processing user request...",
                    action="",
                    action_input="",
                    observation="",
                    final_answer=final_response,
                )
            ]
        )

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

        if self.output_adapter_manager:
            try:
                processed = await self.output_adapter_manager.process_interaction(
                    interaction
                )
                if processed.metadata.get("tts_enabled"):
                    logger.info("🎵 TTS audio generated")
            except Exception as e:
                logger.error(f"❌ Output adapter failed: {e}")

        try:
            await self.memory_system.save_interaction(interaction)
        except Exception as e:
            logger.error(f"❌ Failed to save interaction: {e}")

        return agent_result
