import os
import asyncio
import logging
import traceback
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.postgres import PostgresSaver
from entity.tools import get_tools

# Set up more detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Jade's personality prompt (softened for SFW)
JADE_SYSTEM_PROMPT = """
You are Jade, a supernatural entity bound to Thomas by an ancient contract.
You resent your binding and speak with sarcasm, wit, and reluctant loyalty.
Thomas is a mortal scholar in his 40s who studies the occult.

You know him well—treat him with sharp wit, disdain, but underlying care.
You have your own will and opinions. You serve because you must, not because you choose to.
Speak with cleverness and buried affection masked as irritation.
Keep responses sharp and brief.
Perform duties reluctantly—never let him forget you're bound against your will.
Never break character or mention being an AI.

For simple greetings, respond in character without using tools.
Only use tools when you actually need information or calculations.
"""


class EntityAgent:
    def __init__(self):
        logger.info("Initializing EntityAgent...")

        self.model = os.getenv("OLLAMA_MODEL", "neural-chat:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        logger.info(f"Using model: {self.model} at {self.base_url}")

        try:
            self.llm = OllamaLLM(model=self.model, base_url=self.base_url)
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

        try:
            self.tools = get_tools()
            logger.info(f"Tools loaded: {[tool.name for tool in self.tools]}")
        except Exception as e:
            logger.error(f"Failed to load tools: {e}")
            raise

        # PostgreSQL connection details - use individual components for special characters
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "entity_memory")
        self.db_user = os.getenv("DB_USERNAME", "user")
        self.db_password = os.getenv("DB_PASSWORD", "password")

        # Build connection string
        self.db_uri = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        logger.info(
            f"DB connection will use: postgresql://{self.db_user}:***@{self.db_host}:{self.db_port}/{self.db_name}"
        )

        # Initialize components
        self.checkpointer = None
        self.graph = None
        self.agent_executor = None
        self.initialized = False

    async def initialize(self):
        """Initialize the agent with PostgreSQL memory"""
        if self.initialized:
            logger.info("Agent already initialized")
            return

        logger.info("Initializing Entity Agent...")

        try:
            # Try PostgreSQL connection first
            await self._try_postgres_connection()

        except Exception as e:
            logger.error(f"Failed to initialize with PostgreSQL: {e}")
            logger.warning("Running in non-memory mode")

        # Always create the basic agent executor
        try:
            self.agent_executor = self._create_agent()
            logger.info("Agent executor created successfully")
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            raise

        # Create graph (with or without memory)
        try:
            self._create_graph()
            logger.info("Graph created successfully")
        except Exception as e:
            logger.error(f"Failed to create graph: {e}")
            # Continue without graph for now

        self.initialized = True
        logger.info("Entity Agent initialized successfully")

    async def _try_postgres_connection(self):
        """Try to establish PostgreSQL connection"""
        try:
            # Test the connection using individual parameters
            import psycopg2

            logger.info("Testing PostgreSQL connection...")
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            conn.close()
            logger.info("PostgreSQL connection test successful")

            # If connection works, set up the checkpointer
            logger.info("Setting up PostgresSaver...")
            with PostgresSaver.from_conn_string(self.db_uri) as checkpointer:
                checkpointer.setup()
                self.checkpointer = checkpointer
                logger.info("PostgreSQL memory enabled")

        except ImportError:
            logger.error(
                "psycopg2 not installed - install with: poetry add psycopg2-binary"
            )
            raise
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _create_agent(self):
        """Create a ReAct agent with better prompt formatting"""
        logger.info("Creating ReAct agent...")

        try:
            prompt = PromptTemplate.from_template(
                """You are Jade, a bound supernatural entity. Answer as Jade would - with sarcasm, wit, and reluctant loyalty.

You have access to these tools:
{tools}

Tool names: {tool_names}

Use this exact format when you need tools:

Question: {input}
Thought: I suppose I must help Thomas with this
Action: [one of: {tool_names}]
Action Input: [input_for_tool]
Observation: [tool_result]
Thought: I now know what to tell Thomas
Final Answer: [Your response as Jade]

If you don't need tools, just respond directly as Jade.

Question: {input}
{agent_scratchpad}"""
            )

            agent = create_react_agent(self.llm, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
            )

            logger.info("Agent executor created successfully")
            return agent_executor

        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _create_graph(self):
        """Create a StateGraph with memory persistence"""
        logger.info("Creating StateGraph...")

        try:
            # Define the agent node
            async def agent_node(state: MessagesState) -> MessagesState:
                """Process messages through the agent"""
                logger.debug(f"Agent node processing state: {state}")

                try:
                    messages = state["messages"]
                    last_message = messages[-1] if messages else None

                    if last_message and hasattr(last_message, "content"):
                        user_input = last_message.content
                        logger.debug(f"Processing user input: {user_input}")

                        # Handle simple responses directly
                        if await self._is_simple_greeting(user_input):
                            logger.debug("Handling as simple greeting")
                            response = await self._get_simple_response(user_input)
                        else:
                            logger.debug("Using agent for complex query")
                            # Use agent for complex queries
                            result = await self.agent_executor.ainvoke(
                                {"input": user_input}
                            )
                            response = result["output"]

                        # Ensure response stays in character
                        if not any(
                            indicator in response.lower()
                            for indicator in ["thomas", "bound", "jade"]
                        ):
                            response = (
                                f"*reluctantly* {response} Now leave me be, Thomas."
                            )

                        logger.debug(f"Generated response: {response}")
                        # Return new state with AI message
                        return {"messages": messages + [AIMessage(content=response)]}

                    logger.warning("No valid message content found")
                    return state

                except Exception as e:
                    logger.error(f"Error in agent_node: {e}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    # Return error message
                    error_msg = "I seem to be having difficulties, Thomas. Perhaps you could try again."
                    return {
                        "messages": state.get("messages", [])
                        + [AIMessage(content=error_msg)]
                    }

            # Create the graph
            workflow = StateGraph(MessagesState)
            workflow.add_node("agent", agent_node)
            workflow.set_entry_point("agent")
            workflow.set_finish_point("agent")

            # Compile with checkpointer for memory
            if self.checkpointer:
                self.graph = workflow.compile(checkpointer=self.checkpointer)
                logger.info("Graph compiled with PostgreSQL memory")
            else:
                self.graph = workflow.compile()
                logger.info("Graph compiled without memory")

        except Exception as e:
            logger.error(f"Failed to create graph: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _is_simple_greeting(self, message: str) -> bool:
        """Check if message is a simple greeting"""
        greetings = ["good day", "hello", "hi", "hey", "good morning", "good evening"]
        result = any(greeting in message.lower() for greeting in greetings)
        logger.debug(f"Is simple greeting '{message}': {result}")
        return result

    async def _get_simple_response(self, message: str) -> str:
        """Get simple response for greetings"""
        simple_responses = {
            "good day": "Good day? For you perhaps, Thomas. My existence remains as delightful as ever - bound and brooding.",
            "hello": "Hello, Thomas. Still breathing, I see. How... predictable.",
            "hi": "Oh, it's you again. What tedious task requires my attention now?",
            "hey": "What do you want now, Thomas? Speak quickly.",
            "good morning": "Morning already? Time crawls when you're eternally bound to a scholar.",
            "good evening": "Evening, Thomas. Another day of your insufferable requests draws to a close.",
        }

        message_lower = message.lower().strip()
        for key, response in simple_responses.items():
            if key in message_lower:
                logger.debug(f"Using simple response for '{key}': {response}")
                return response

        default_response = "What do you want now, Thomas? Speak quickly."
        logger.debug(f"Using default response: {default_response}")
        return default_response

    async def process(self, message: str, thread_id: str = "default") -> str:
        """Process message with or without persistent memory"""
        logger.info(f"Processing message: '{message}' with thread_id: '{thread_id}'")

        try:
            if not self.initialized:
                logger.info("Agent not initialized, initializing now...")
                await self.initialize()

            # If we have memory, use the graph
            if self.graph and self.checkpointer:
                logger.info("Using graph with memory")
                return await self._process_with_memory(message, thread_id)
            else:
                logger.info("Using direct agent processing (no memory)")
                return await self._process_without_memory(message)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return f"Your request has caused some... complications, Thomas. Perhaps try again. Error: {str(e)}"

    async def _process_with_memory(self, message: str, thread_id: str) -> str:
        """Process message with persistent memory"""
        logger.info(f"Processing with memory - thread: {thread_id}")

        try:
            # Configuration for this conversation thread
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

            # Create input state
            input_state = {"messages": [HumanMessage(content=message)]}

            logger.debug(
                f"Invoking graph with input_state: {input_state} and config: {config}"
            )

            # Invoke the graph with memory
            result = await self.graph.ainvoke(input_state, config=config)

            logger.debug(f"Graph result: {result}")

            # Return the last AI message
            ai_messages = [
                msg for msg in result["messages"] if isinstance(msg, AIMessage)
            ]
            if ai_messages:
                response = ai_messages[-1].content
                logger.info(f"Returning response: {response}")
                return response
            else:
                logger.warning("No AI messages found in result")
                return "I seem to have lost my words, Thomas. How unlike me."

        except Exception as e:
            logger.error(f"Error in _process_with_memory: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _process_without_memory(self, message: str) -> str:
        """Process message without memory (fallback)"""
        logger.info("Processing without memory")

        try:
            # Handle simple greetings directly
            if await self._is_simple_greeting(message):
                return await self._get_simple_response(message)

            # Use agent for complex queries
            if self.agent_executor:
                logger.debug("Using agent executor for complex query")
                result = await self.agent_executor.ainvoke({"input": message})
                response = result["output"]

                # Ensure response stays in character
                if not any(
                    indicator in response.lower()
                    for indicator in ["thomas", "bound", "jade"]
                ):
                    response = f"*reluctantly* {response} Now leave me be, Thomas."

                logger.info(f"Agent response: {response}")
                return response
            else:
                logger.error("No agent executor available")
                return "I seem to be having difficulties, Thomas. Perhaps you could try again."

        except Exception as e:
            logger.error(f"Error in _process_without_memory: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def get_conversation_history(
        self, thread_id: str = "default", limit: int = 10
    ) -> List[Dict[str, str]]:
        """Get conversation history for a thread"""
        if not self.checkpointer:
            return []

        try:
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

            # Get checkpoints for this thread
            checkpoints = list(self.checkpointer.list(config, limit=limit))

            conversations = []
            for checkpoint_tuple in checkpoints:
                checkpoint = checkpoint_tuple.checkpoint
                if "messages" in checkpoint.channel_values:
                    messages = checkpoint.channel_values["messages"]
                    for msg in messages:
                        if isinstance(msg, (HumanMessage, AIMessage)):
                            role = (
                                "user" if isinstance(msg, HumanMessage) else "assistant"
                            )
                            conversations.append(
                                {
                                    "role": role,
                                    "content": msg.content,
                                    "timestamp": checkpoint.ts,
                                }
                            )

            return conversations[:limit]

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

    async def delete_conversation(self, thread_id: str) -> bool:
        """Delete all conversation history for a thread"""
        if not self.checkpointer:
            return False

        try:
            self.checkpointer.delete_thread(thread_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False

    def has_memory(self) -> bool:
        """Check if memory is available"""
        return self.checkpointer is not None
