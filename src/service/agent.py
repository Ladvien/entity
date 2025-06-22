from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import re
from dataclasses import dataclass
from rich.text import Text
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.base import BaseLanguageModel

from src.memory.memory_system import MemorySystem
from src.service.config import EntityConfig
from src.shared.agent_result import AgentResult
from src.tools.tools import ToolManager
from src.adapters import OutputAdapterManager

logger = logging.getLogger(__name__)


@dataclass
class ReActStep:
    thought: str
    action: str
    action_input: str
    observation: str
    final_answer: str

    def format_rich(self) -> Text:
        text = Text()
        text.append("Thought: ", style="cyan").append(f"{self.thought}\n")
        text.append("Action: ", style="blue").append(f"{self.action}\n")
        text.append("Action Input: ", style="magenta").append(f"{self.action_input}\n")
        text.append("Observation: ", style="yellow").append(f"{self.observation}\n")
        text.append("Final Answer: ", style="green").append(f"{self.final_answer}")
        return text


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


class PromptBuilder:
    def __init__(self, config: EntityConfig, tool_manager: ToolManager):
        self.config = config
        self.tool_manager = tool_manager

    def build_prompt_vars(self, message: str, memory_context: str) -> Dict[str, str]:
        tools = self.tool_manager.get_all_tools()
        prompt_vars = {
            "input": message.strip(),
            "agent_scratchpad": "",
            "tools": "\n".join(f"{tool.name}: {tool.description}" for tool in tools),
            "tool_names": ", ".join(tool.name for tool in tools),
        }
        if memory_context:
            prompt_vars["memory_context"] = memory_context.strip()
        return prompt_vars

    def format_prompt(self, prompt_vars: Dict[str, str]) -> str:
        missing_vars = set(self.config.prompts.variables) - set(prompt_vars)
        if missing_vars:
            logger.warning(f"⚠️ Missing prompt variables: {missing_vars}")
        try:
            return self.config.prompts.base_prompt.strip().format(**prompt_vars)
        except KeyError as e:
            logger.error(f"❌ Failed to render base prompt. Missing key: {e}")
            return (
                prompt_vars.get("memory_context", "")
                + "\n\n"
                + prompt_vars.get("input", "")
            )


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
        self.prompt_builder = PromptBuilder(config, tool_manager)

    async def initialize(self):
        tools = self.tool_registry.get_all_tools()
        prompt = PromptTemplate(
            input_variables=self.config.prompts.variables,
            template=self.config.prompts.base_prompt.strip(),
        )
        logger.debug(
            f"🛠️ Initializing agent with {len(tools)} tools and prompt: {prompt.template}"
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

    async def chat(
        self, message: str, thread_id: str = "default", use_tools: bool = True
    ) -> AgentResult:
        start_time = datetime.utcnow()
        logger.info(
            f"💬 Processing message: '{message[:100]}{'...' if len(message) > 100 else ''}'"
        )

        memory_context = await self.memory_builder.build_context(message, thread_id)
        enhanced_input = {
            "input": f"{memory_context}\n\n{message}" if memory_context else message
        }

        raw_output, final_response, tools_used, token_count, intermediate_steps = (
            "",
            "",
            [],
            0,
            [],
        )

        if use_tools and self.agent_executor:
            logger.info("🤖 Running through agent executor with tools...")
            result = await self.agent_executor.ainvoke(enhanced_input)
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
        else:
            prompt_vars = self.prompt_builder.build_prompt_vars(message, memory_context)
            formatted_prompt = self.prompt_builder.format_prompt(prompt_vars)
            raw_output = self.llm.invoke(formatted_prompt)
            final_response = raw_output

        if not final_response.strip():
            logger.error("❌ Empty response from LLM")
            final_response = (
                "I apologize, but I seem to be having trouble responding right now."
            )

        return AgentResult(
            raw_input=message,
            raw_output=raw_output,
            final_response=final_response,
            tools_used=tools_used,
            token_count=token_count,
            memory_context=memory_context,
            intermediate_steps=intermediate_steps,
            thread_id=thread_id,
            timestamp=start_time,
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

    def extract_final_answer(self, output: str) -> str:
        match = re.search(
            r"Final Answer:\s*(.*)", output, flags=re.IGNORECASE | re.DOTALL
        )
        return match.group(1).strip() if match else output.strip()

    async def cleanup(self):
        logger.info("🧹 Agent cleanup completed")
