# Rewriting the EntityAgent class with improvements based on the review

import asyncio
import logging
import time
import traceback
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document
from langchain.agents import create_openai_functions_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.agents import AgentExecutor, create_react_agent

from src.tool_registry import ToolRegistry, register_memory_tools
from src.config import EntitySystemConfig
from src.tools import get_tools
from src.memory import VectorMemorySystem

logger = logging.getLogger(__name__)


class EntityAgent:
    def __init__(self, config: EntitySystemConfig):
        self.config = config
        self.settings = config  # Ensure settings is initialized
        self.llm = OllamaLLM(**self.settings.ollama.model_dump())
        self.memory_system = VectorMemorySystem(self.settings.memory)

        self.model = self.config.ollama.model
        self.base_url = self.config.ollama.base_url

        self.tool_registry = ToolRegistry()
        self.tool_registry.set_context({"memory": self.memory_system})
        self.tool_registry.register_factory(register_memory_tools)
        self.tools = self.tool_registry.get_tools()
        logger.info(f"🧰 Tools loaded: {[tool.name for tool in self.tools]}")

        self.checkpointer = None
        self.graph = None
        self.agent_executor = None
        self.initialized = False

    async def initialize(self):
        if self.initialized:
            logger.info("Agent already initialized")
            return

        logger.info("Initializing Entity Agent...")

        try:
            await self.memory_system.initialize()
            logger.info("✅ Vector memory system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector memory: {e}")
            raise

        try:
            await self._try_postgres_connection()
        except Exception as e:
            logger.warning("PostgreSQL checkpointing unavailable, continuing without.")

        self.agent_executor = self._create_agent()
        if self.agent_executor is None:
            raise RuntimeError("AgentExecutor could not be initialized")

        try:
            self._create_graph()
        except Exception as e:
            logger.error(f"Graph creation failed: {e}")
            raise

        self.initialized = True
        logger.info("Entity Agent initialized successfully")

    async def _try_postgres_connection(self):
        import psycopg2

        conn = psycopg2.connect(
            host=self.settings.database.host,
            port=self.settings.database.port,
            database=self.settings.database.name,
            user=self.settings.database.username,
            password=self.settings.database.password,
        )
        conn.close()

        self.checkpointer = PostgresSaver.from_conn_string(
            self.settings.database.connection_string
        )
        self.checkpointer.setup()
        logger.info("PostgreSQL checkpointing enabled")

    def _create_agent(self):
        # Fixed prompt template with all required variables
        prompt_template = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
            template=f"""{self.settings.prompts.base_prompt}

TOOLS:
{{tools}}

Available tool names: {{tool_names}}

For simple conversations, respond directly as Jade.
Only use tools if you absolutely must search for information or calculate something.

If using a tool, use this format:
Thought: I need to use a tool because...
Action: tool_name
Action Input: specific_input
Observation: [result will appear here]
Final Answer: [your response as Jade]

If no tools are needed, respond directly as Jade.

Question: {{input}}
{{agent_scratchpad}}""",
        )

        agent = create_react_agent(self.llm, self.tools, prompt_template)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.settings.debug,
            handle_parsing_errors=True,
            max_iterations=3,  # Reduced from 20
            max_execution_time=30,  # Reduced from 120
            early_stopping_method="generate",  # Stop early if possible
        )

    def _create_graph(self):
        async def agent_node(state: MessagesState) -> MessagesState:
            messages = state["messages"]
            last_message = messages[-1] if messages else None

            if not last_message or not hasattr(last_message, "content"):
                return state

            user_input = last_message.content
            memory_context = await self.memory_system.get_memory_context(user_input)

            enhanced_input = (
                f"{memory_context}\n\nCurrent input: {user_input}"
                if memory_context
                else user_input
            )

            start_time = time.monotonic()
            max_time = 30  # Reduced from 120
            max_iterations = 3  # Reduced from 20
            result = None

            for iteration in range(max_iterations):
                elapsed = time.monotonic() - start_time
                if elapsed > max_time:
                    logger.warning("⏳ Execution timed out")
                    response = "Agent stopped due to time limit. *sarcastically* How delightful for you, Thomas."
                    break

                try:
                    result = await asyncio.wait_for(
                        self.agent_executor.ainvoke({"input": enhanced_input}),
                        timeout=10,  # Shorter individual timeout
                    )
                    response = result["output"]
                    steps = result.get("intermediate_steps", [])
                    logger.info(
                        f"✅ Agent completed in {iteration+1} iterations, {len(steps)} steps."
                    )
                    break
                except asyncio.TimeoutError:
                    logger.warning(
                        f"⏱️ agent_executor timed out on iteration {iteration+1}"
                    )
                except Exception as e:
                    logger.warning(f"Agent iteration {iteration+1} failed: {e}")
                    await asyncio.sleep(0.5)

            else:
                response = "Agent stopped due to iteration limit. *sarcastically* How delightful for you, Thomas."

            try:
                await self.memory_system.store_conversation(
                    user_input, response, "default"
                )
            except Exception as e:
                logger.warning(f"Could not store memory: {e}")

            response = self._adjust_response_personality(response)
            return {"messages": messages + [AIMessage(content=response)]}

        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", agent_node)
        workflow.set_entry_point("agent")
        workflow.set_finish_point("agent")

        if self.checkpointer:
            self.graph = workflow.compile(checkpointer=self.checkpointer)
        else:
            self.graph = workflow.compile()

    async def _is_simple_conversation(self, message: str) -> bool:
        """Check if this is a simple conversation that doesn't need tools"""
        message_lower = message.lower().strip()

        # Patterns that definitely don't need tools
        simple_patterns = [
            "hey",
            "hi",
            "hello",
            "good day",
            "good morning",
            "good evening",
            "what do you want",
            "speak quickly",
            "tell me",
            "do not tell me",
            "bitch",
            "stop",
            "continue",
            "truth",
        ]

        # If message is short and contains simple words, handle directly
        if len(message) < 100 and any(
            pattern in message_lower for pattern in simple_patterns
        ):
            return True

        return False

    async def _get_direct_jade_response(self, message: str) -> str:
        """Get a direct response from Jade without using the agent loop"""
        memory_context = await self.memory_system.get_memory_context(message)

        # Create a simple prompt for direct response
        direct_prompt = f"""{self.settings.prompts.base_prompt}

Previous context: {memory_context if memory_context else "No relevant memories."}

Thomas just said: "{message}"

Respond as Jade would - with sarcasm, wit, and reluctant service. Keep it brief and in character."""

        try:
            # Direct LLM call without agent wrapper
            response = await self.llm.ainvoke(direct_prompt)
            return self._adjust_response_personality(response)
        except Exception as e:
            logger.error(f"Direct response failed: {e}")
            return "Something's wrong with my voice, Thomas. How inconvenient for you."

    def _adjust_response_personality(self, response: str) -> str:
        if self.settings.entity.response_brevity > 0.8 and len(response) > 100:
            sentences = response.split(". ")
            response = ". ".join(sentences[:2]) + "."

        keywords = ["thomas", "bound", "jade"]
        if not any(k in response.lower() for k in keywords):
            if self.settings.entity.sarcasm_level > 0.7:
                response += " *sarcastically* How delightful for you, Thomas."
            elif self.settings.entity.anger_level > 0.7:
                response += " Now leave me be."
            else:
                response += " There. Your task is complete."
        return response

    async def process(self, message: str, thread_id: str = "default") -> str:
        if self.agent_executor is None:
            raise RuntimeError("AgentExecutor not initialized")

        if not self.initialized:
            await self.initialize()

        if self.graph and self.checkpointer:
            return await self._process_with_checkpointing(message, thread_id)
        return await self._process_without_checkpointing(message, thread_id)

    async def _process_with_checkpointing(self, message: str, thread_id: str) -> str:
        input_state = {"messages": [HumanMessage(content=message)]}
        result = await self.graph.ainvoke(
            input_state, config={"configurable": {"thread_id": thread_id}}
        )
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        return (
            ai_messages[-1].content
            if ai_messages
            else "I seem to have lost my words, Thomas."
        )

    async def _process_without_checkpointing(self, message: str, thread_id: str) -> str:
        # Check if this is a simple conversation first
        if await self._is_simple_conversation(message):
            logger.info("🎭 Using direct response for simple conversation")
            response = await self._get_direct_jade_response(message)
        else:
            logger.info("🔧 Using agent executor for complex query")
            memory_context = await self.memory_system.get_memory_context(
                message, thread_id
            )
            enhanced_input = (
                f"{memory_context}\n\nCurrent input: {message}"
                if memory_context
                else message
            )

            try:
                result = await asyncio.wait_for(
                    self.agent_executor.ainvoke({"input": enhanced_input}),
                    timeout=30,  # Hard timeout
                )
                response = result["output"]
                response = self._adjust_response_personality(response)
            except asyncio.TimeoutError:
                logger.warning("⏰ Agent executor timed out, using fallback")
                response = await self._get_direct_jade_response(message)
            except Exception as e:
                logger.error(f"Agent executor failed: {e}")
                response = await self._get_direct_jade_response(message)

        # Store the conversation
        await self.memory_system.store_conversation(message, response, thread_id)
        return response

    def has_memory(self) -> bool:
        return self.memory_system is not None

    async def close(self):
        if self.memory_system:
            await self.memory_system.close()
        if self.checkpointer:
            pass  # Placeholder for checkpointer close if needed

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get stats about memory and personality config"""
        try:
            stats = await self.memory_system.get_memory_stats()
            stats["agent_config"] = {
                "model": self.model,
                "base_url": self.base_url,
                "personality": {
                    "sarcasm_level": self.settings.entity.sarcasm_level,
                    "loyalty_level": self.settings.entity.loyalty_level,
                    "anger_level": self.settings.entity.anger_level,
                    "wit_level": self.settings.entity.wit_level,
                },
                "conversation_checkpointing": self.checkpointer is not None,
                "vector_memory": True,
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    async def get_conversation_history(
        self, thread_id: Optional[str] = None, limit: int = 10
    ) -> List[str]:
        thread = thread_id or "default"
        try:
            results = await self.memory_system.search_memory(
                query="", thread_id=thread, k=limit
            )

            history = []
            for doc in results:
                if isinstance(doc, Document):
                    history.append(doc.page_content)
                elif isinstance(doc, dict) and isinstance(doc.get("page_content"), str):
                    history.append(doc["page_content"])
                elif isinstance(doc, str):
                    history.append(doc)
                else:
                    history.append(str(doc))  # catch-all fallback

            return history

        except Exception as e:
            logger.error(f"❌ Failed to fetch conversation history: {e}")
            return []
