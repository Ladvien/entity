# entity/agent.py
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
from entity.memory import VectorMemorySystem
from entity.config import Settings, get_settings

# Set up logging
logger = logging.getLogger(__name__)


class EntityAgent:
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        logger.info("Initializing EntityAgent with configuration...")

        # Ollama configuration
        self.model = self.settings.ollama.model
        self.base_url = self.settings.ollama.base_url

        logger.info(f"Using model: {self.model} at {self.base_url}")

        try:
            # Initialize LLM with configuration
            self.llm = OllamaLLM(
                model=self.model,
                base_url=self.base_url,
                temperature=self.settings.ollama.temperature,
                top_p=self.settings.ollama.top_p,
                top_k=self.settings.ollama.top_k,
                repeat_penalty=self.settings.ollama.repeat_penalty,
            )
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

        # Initialize memory system
        try:
            self.memory_system = VectorMemorySystem(settings=self.settings)
            logger.info("Memory system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            raise

        # PostgreSQL connection for LangGraph checkpointing
        self.db_uri = self.settings.database.connection_string
        logger.info(
            f"DB connection will use: {self.db_uri.replace(self.settings.database.password, '***')}"
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

        # Initialize vector memory system first
        try:
            await self.memory_system.initialize()
            logger.info("✅ Vector memory system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector memory: {e}")
            raise

        # Try PostgreSQL connection for conversation checkpointing
        try:
            await self._try_postgres_connection()
        except Exception as e:
            logger.error(f"Failed to initialize with PostgreSQL checkpointing: {e}")
            logger.warning("Running conversation checkpointing in memory-only mode")

        # Always create the basic agent executor
        try:
            self.agent_executor = self._create_agent()
            logger.info("Agent executor created successfully")
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            raise

        # Create graph (with or without persistent checkpointing)
        try:
            self._create_graph()
            logger.info("Graph created successfully")
        except Exception as e:
            logger.error(f"Failed to create graph: {e}")
            # Continue without graph for now

        self.initialized = True
        logger.info("Entity Agent initialized successfully")

    async def _try_postgres_connection(self):
        """Try to establish PostgreSQL connection for checkpointing"""
        try:
            import psycopg2

            logger.info("Testing PostgreSQL connection for checkpointing...")
            conn = psycopg2.connect(
                host=self.settings.database.host,
                port=self.settings.database.port,
                database=self.settings.database.name,
                user=self.settings.database.username,
                password=self.settings.database.password,
            )
            conn.close()
            logger.info("PostgreSQL connection test successful")

            # If connection works, set up the checkpointer
            logger.info("Setting up PostgresSaver...")
            with PostgresSaver.from_conn_string(self.db_uri) as checkpointer:
                checkpointer.setup()
                self.checkpointer = checkpointer
                logger.info("PostgreSQL conversation checkpointing enabled")

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
        """Create a ReAct agent with enhanced prompt"""
        logger.info("Creating ReAct agent...")

        try:
            # Get enhanced system prompt from settings
            enhanced_prompt = self.settings.get_enhanced_system_prompt()

            prompt = PromptTemplate.from_template(
                f"""{enhanced_prompt}

You have access to these tools:
{{tools}}

Tool names: {{tool_names}}

Use this exact format when you need tools:

Question: {{input}}
Thought: I suppose I must help Thomas with this
Action: [one of: {{tool_names}}]
Action Input: [input_for_tool]
Observation: [tool_result]
Thought: I now know what to tell Thomas
Final Answer: [Your response as Jade]

If you don't need tools, just respond directly as Jade.

Question: {{input}}
{{agent_scratchpad}}"""
            )

            agent = create_react_agent(self.llm, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=self.settings.debug,
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
                """Process messages through the agent with memory"""
                logger.debug(f"Agent node processing state: {state}")

                try:
                    messages = state["messages"]
                    last_message = messages[-1] if messages else None

                    if last_message and hasattr(last_message, "content"):
                        user_input = last_message.content
                        logger.debug(f"Processing user input: {user_input}")

                        # Get memory context for this input
                        memory_context = await self.memory_system.get_memory_context(
                            user_input
                        )

                        # Handle simple responses directly or use agent
                        if await self._is_simple_greeting(user_input):
                            logger.debug("Handling as simple greeting")
                            response = await self._get_simple_response(user_input)
                        else:
                            logger.debug("Using agent for complex query")

                            # Enhance input with memory context if available
                            enhanced_input = user_input
                            if memory_context:
                                enhanced_input = (
                                    f"{memory_context}\n\nCurrent input: {user_input}"
                                )

                            # Use agent for complex queries
                            result = await self.agent_executor.ainvoke(
                                {"input": enhanced_input}
                            )
                            response = result["output"]

                        # Store conversation in memory system
                        try:
                            # Extract thread_id from config if available (you might need to pass this)
                            thread_id = (
                                "default"  # You might want to extract this from state
                            )
                            await self.memory_system.store_conversation(
                                user_input, response, thread_id
                            )
                        except Exception as mem_error:
                            logger.warning(
                                f"Failed to store conversation in memory: {mem_error}"
                            )

                        # Apply personality adjustments based on settings
                        response = self._adjust_response_personality(response)

                        logger.debug(f"Generated response: {response}")
                        return {"messages": messages + [AIMessage(content=response)]}

                    logger.warning("No valid message content found")
                    return state

                except Exception as e:
                    logger.error(f"Error in agent_node: {e}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
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

            # Compile with checkpointer for conversation persistence
            if self.checkpointer:
                self.graph = workflow.compile(checkpointer=self.checkpointer)
                logger.info("Graph compiled with PostgreSQL conversation checkpointing")
            else:
                self.graph = workflow.compile()
                logger.info("Graph compiled without conversation checkpointing")

        except Exception as e:
            logger.error(f"Failed to create graph: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _adjust_response_personality(self, response: str) -> str:
        """Adjust response based on personality settings"""
        # Apply brevity setting
        if self.settings.entity.response_brevity > 0.8 and len(response) > 100:
            # Make response more brief for high brevity setting
            sentences = response.split(". ")
            if len(sentences) > 2:
                response = ". ".join(sentences[:2]) + "."

        # Ensure response stays in character based on personality settings
        entity_indicators = ["thomas", "bound", "jade"]
        if not any(indicator in response.lower() for indicator in entity_indicators):
            # Add character-appropriate suffix based on personality
            if self.settings.entity.sarcasm_level > 0.7:
                response = f"{response} *sarcastically* How delightful for you, Thomas."
            elif self.settings.entity.anger_level > 0.7:
                response = f"{response} Now leave me be."
            else:
                response = f"{response} There. Your task is complete."

        return response

    async def _is_simple_greeting(self, message: str) -> bool:
        import re

        greetings = ["good day", "hello", "hi", "hey", "good morning", "good evening"]
        message_lower = message.lower().strip()

        for greeting in greetings:
            if re.search(r"\b" + re.escape(greeting) + r"\b", message_lower):
                return True
        return False

    async def _get_simple_response(self, message: str) -> str:
        """Get simple response for greetings adjusted by personality"""
        base_responses = {
            "good day": "Good day? For you perhaps, Thomas. My existence remains as delightful as ever - bound and brooding.",
            "hello": "Hello, Thomas. Still breathing, I see. How... predictable.",
            "hi": "Oh, it's you again. What tedious task requires my attention now?",
            "hey": "What do you want now, Thomas? Speak quickly.",
            "good morning": "Morning already? Time crawls when you're eternally bound to a scholar.",
            "good evening": "Evening, Thomas. Another day of your insufferable requests draws to a close.",
        }

        message_lower = message.lower().strip()
        for key, response in base_responses.items():
            if key in message_lower:
                # Adjust response based on personality settings
                if self.settings.entity.sarcasm_level > 0.8:
                    response = response.replace(
                        "How... predictable.", "How utterly, devastatingly predictable."
                    )
                elif self.settings.entity.anger_level > 0.8:
                    response = response.replace(
                        "Thomas.", "Thomas, you insufferable fool."
                    )

                logger.debug(f"Using simple response for '{key}': {response}")
                return response

        default_response = "What do you want now, Thomas? Speak quickly."
        logger.debug(f"Using default response: {default_response}")
        return default_response

    async def process(self, message: str, thread_id: str = "default") -> str:
        """Process message with vector memory and optional conversation checkpointing"""
        logger.info(f"Processing message: '{message}' with thread_id: '{thread_id}'")

        try:
            if not self.initialized:
                logger.info("Agent not initialized, initializing now...")
                await self.initialize()

            # If we have conversation checkpointing, use the graph
            if self.graph and self.checkpointer:
                logger.info("Using graph with conversation checkpointing")
                return await self._process_with_checkpointing(message, thread_id)
            else:
                logger.info("Using direct agent processing (with vector memory only)")
                return await self._process_without_checkpointing(message, thread_id)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return f"Your request has caused some... complications, Thomas. Perhaps try again. Error: {str(e)}"

    async def _process_with_checkpointing(self, message: str, thread_id: str) -> str:
        """Process message with persistent conversation checkpointing"""
        logger.info(f"Processing with checkpointing - thread: {thread_id}")

        try:
            # Configuration for this conversation thread
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

            # Create input state
            input_state = {"messages": [HumanMessage(content=message)]}

            logger.debug(
                f"Invoking graph with input_state: {input_state} and config: {config}"
            )

            # Invoke the graph with conversation persistence
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
            logger.error(f"Error in _process_with_checkpointing: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _process_without_checkpointing(self, message: str, thread_id: str) -> str:
        """Process message with vector memory only"""
        logger.info("Processing with vector memory only")

        try:
            # Get memory context
            memory_context = await self.memory_system.get_memory_context(
                message, thread_id
            )

            # Handle simple greetings directly
            if await self._is_simple_greeting(message):
                response = await self._get_simple_response(message)
            else:
                # Use agent for complex queries
                if self.agent_executor:
                    logger.debug("Using agent executor for complex query")

                    # Enhance input with memory context
                    enhanced_input = message
                    if memory_context:
                        enhanced_input = f"{memory_context}\n\nCurrent input: {message}"

                    result = await self.agent_executor.ainvoke(
                        {"input": enhanced_input}
                    )
                    response = result["output"]

                    # Apply personality adjustments
                    response = self._adjust_response_personality(response)
                else:
                    logger.error("No agent executor available")
                    return "I seem to be having difficulties, Thomas. Perhaps you could try again."

            # Store conversation in vector memory
            try:
                await self.memory_system.store_conversation(
                    message, response, thread_id
                )
            except Exception as mem_error:
                logger.warning(f"Failed to store conversation in memory: {mem_error}")

            logger.info(f"Agent response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error in _process_without_checkpointing: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def get_conversation_history(
        self, thread_id: str = "default", limit: int = 10
    ) -> List[Dict[str, str]]:
        """Get conversation history from vector memory system"""
        try:
            conversations = await self.memory_system.get_conversation_history(
                thread_id, limit
            )

            # Format for compatibility
            formatted_conversations = []
            for conv in conversations:
                formatted_conversations.extend(
                    [
                        {
                            "role": "user",
                            "content": conv["user_input"],
                            "timestamp": (
                                conv["timestamp"].isoformat()
                                if hasattr(conv["timestamp"], "isoformat")
                                else str(conv["timestamp"])
                            ),
                        },
                        {
                            "role": "assistant",
                            "content": conv["ai_response"],
                            "timestamp": (
                                conv["timestamp"].isoformat()
                                if hasattr(conv["timestamp"], "isoformat")
                                else str(conv["timestamp"])
                            ),
                        },
                    ]
                )

            return formatted_conversations

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

    async def delete_conversation(self, thread_id: str) -> bool:
        """Delete all conversation history for a thread"""
        try:
            # Delete from vector memory
            success = await self.memory_system.delete_thread_memories(thread_id)

            # Also delete from checkpointer if available
            if self.checkpointer:
                try:
                    self.checkpointer.delete_thread(thread_id)
                except Exception as e:
                    logger.warning(f"Failed to delete from checkpointer: {e}")

            return success
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            stats = await self.memory_system.get_memory_stats()

            # Add agent-specific stats
            stats.update(
                {
                    "agent_config": {
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
                }
            )

            return stats
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    def has_memory(self) -> bool:
        """Check if any memory system is available"""
        return self.memory_system is not None

    async def close(self):
        """Close all connections"""
        if self.memory_system:
            await self.memory_system.close()
        if self.checkpointer:
            # Close checkpointer connections if needed
            pass
