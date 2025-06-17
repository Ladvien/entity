# entity/tools.py (updated with memory tool)

from langchain_core.tools import tool
import httpx
import json
import ast
import operator
import asyncio
from typing import List, Dict, Any, Optional


# Import your memory system
try:
    from entity.memory import VectorMemorySystem
    from entity.config import get_settings

    # Global memory instance
    _memory_system = None

    async def get_memory_system():
        """Get or create global memory system instance"""
        global _memory_system
        if _memory_system is None:
            settings = get_settings()
            _memory_system = VectorMemorySystem(settings=settings)
            await _memory_system.initialize()
        return _memory_system

except ImportError:
    # Fallback if memory system not available
    async def get_memory_system():
        return None


@tool
def web_search(query: str) -> str:
    """Search the web for information"""
    try:
        # Try multiple search approaches

        # First try DuckDuckGo instant answers
        url = (
            f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&no_redirect=1"
        )
        response = httpx.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()

            # Check for abstract text
            if data.get("AbstractText"):
                return f"Search result: {data['AbstractText']}"

            # Check for definition
            if data.get("Definition"):
                return f"Definition: {data['Definition']}"

            # Check for related topics
            if data.get("RelatedTopics"):
                results = []
                for topic in data["RelatedTopics"][:3]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append(topic["Text"])
                if results:
                    return f"Search results: {' | '.join(results)}"

            # Check for answer
            if data.get("Answer"):
                return f"Answer: {data['Answer']}"

        # Fallback response for simple queries
        if "good day" in query.lower():
            return "A good day typically refers to a pleasant, positive, or successful day. It's a common greeting meaning 'have a pleasant day' or can describe a day that went well."

        if "chrome" in query.lower() and "ubuntu" in query.lower():
            return "To install Chrome on Ubuntu: 1) Download the .deb package from google.com/chrome 2) Run 'sudo dpkg -i google-chrome-stable_current_amd64.deb' 3) Fix dependencies with 'sudo apt-get install -f' if needed."

        return f"No specific results found for '{query}'. Try rephrasing your search."

    except Exception as e:
        return f"Search temporarily unavailable: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions safely"""
    try:
        # Clean the expression
        expression = expression.strip()

        # Remove common text that might be included
        expression = expression.replace("calculate", "").replace("what is", "").strip()

        # Handle simple cases
        if "=" in expression:
            expression = expression.split("=")[0].strip()

        # Safe evaluation using ast
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            elif isinstance(node, ast.Num):  # Fallback for older Python
                return node.n
            elif isinstance(node, ast.BinOp):
                return allowed_operators[type(node.op)](
                    eval_expr(node.left), eval_expr(node.right)
                )
            elif isinstance(node, ast.UnaryOp):
                return allowed_operators[type(node.op)](eval_expr(node.operand))
            else:
                raise TypeError(f"Unsupported operation: {node}")

        tree = ast.parse(expression, mode="eval")
        result = eval_expr(tree.body)
        return f"{expression} = {result}"

    except Exception as e:
        return f"Cannot calculate '{expression}'. Error: {str(e)}"


@tool
def recall_memory(query: str, thread_id: str = "default", limit: int = 3) -> str:
    """Search and recall relevant memories from previous conversations"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            memory_system = loop.run_until_complete(get_memory_system())

            if memory_system is None:
                return "Memory system not available."

            # Get relevant memories
            memories = loop.run_until_complete(
                memory_system.get_relevant_memories(query, thread_id, limit)
            )

            if not memories:
                return f"No relevant memories found for '{query}'."

            # Format memories for the agent
            memory_text = []
            for i, memory in enumerate(memories, 1):
                content = memory.get("content", "")
                emotion = memory.get("emotion", "neutral")
                similarity = memory.get("similarity", 0.0)

                # Truncate long memories
                if len(content) > 150:
                    content = content[:150] + "..."

                memory_text.append(
                    f"{i}. [{emotion}] {content} (relevance: {similarity:.2f})"
                )

            return f"Found {len(memories)} relevant memories:\n" + "\n".join(
                memory_text
            )

        finally:
            loop.close()

    except Exception as e:
        return f"Memory recall failed: {str(e)}"


@tool
def store_memory(
    content: str, memory_type: str = "important", thread_id: str = "default"
) -> str:
    """Store important information in memory for later recall"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            memory_system = loop.run_until_complete(get_memory_system())

            if memory_system is None:
                return "Memory system not available."

            # Store as a special memory entry
            loop.run_until_complete(
                memory_system.store_conversation(
                    f"IMPORTANT: {content}",
                    f"Jade noted: This information has been stored for future reference.",
                    thread_id,
                )
            )

            return f"Information stored in memory: '{content[:100]}...'"

        finally:
            loop.close()

    except Exception as e:
        return f"Memory storage failed: {str(e)}"


@tool
def get_conversation_summary(thread_id: str = "default", limit: int = 10) -> str:
    """Get a summary of recent conversation history"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            memory_system = loop.run_until_complete(get_memory_system())

            if memory_system is None:
                return "Memory system not available."

            # Get recent conversations
            conversations = loop.run_until_complete(
                memory_system.get_conversation_history(thread_id, limit)
            )

            if not conversations:
                return f"No conversation history found for thread '{thread_id}'."

            # Format summary
            summary_parts = []
            for conv in conversations[-5:]:  # Last 5 conversations
                user_input = conv.get("user_input", "")[:50]
                ai_response = conv.get("ai_response", "")[:50]

                if user_input and ai_response:
                    summary_parts.append(
                        f"Thomas: {user_input}... → Jade: {ai_response}..."
                    )

            return f"Recent conversation summary:\n" + "\n".join(summary_parts)

        finally:
            loop.close()

    except Exception as e:
        return f"Conversation summary failed: {str(e)}"


@tool
def simple_response(input_text: str) -> str:
    """Provide simple responses for basic greetings and casual conversation"""
    text = input_text.lower().strip()

    greetings = ["hello", "hi", "good day", "good morning", "good evening", "hey"]
    if any(greeting in text for greeting in greetings):
        return "A greeting. Respond in character as Jade with sarcasm and reluctant acknowledgment."

    if "how are you" in text:
        return "A question about wellbeing. Respond as Jade with disdain but hint at deeper feelings."

    if "thank you" in text or "thanks" in text:
        return "Gratitude expressed. Jade should respond with scorn but perhaps grudging acceptance."

    return f"Simple conversational input: {input_text}"


def get_tools():
    """Return list of available tools including memory tools"""
    return [
        web_search,
        calculator,
        recall_memory,
        store_memory,
        get_conversation_summary,
        simple_response,
    ]
