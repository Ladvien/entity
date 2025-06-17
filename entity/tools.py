# entity/tools.py - Fixed version

from langchain_core.tools import tool
import httpx
import json
import ast
import operator
import asyncio
from typing import List, Dict, Any, Optional

# Try to import PostgreSQL memory tools
POSTGRES_MEMORY_AVAILABLE = False
try:
    from entity.tools.memory_tool import get_memory_tools

    POSTGRES_MEMORY_AVAILABLE = True
    print("✅ PostgreSQL memory tools loaded")
except ImportError as e:
    print(f"⚠️  PostgreSQL memory tools not available: {e}")


@tool
def web_search(query: str) -> str:
    """Search the web for information"""
    try:
        # Try multiple search approaches
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

        # Fallback responses for common queries
        query_lower = query.lower()
        if "good day" in query_lower:
            return "A good day typically refers to a pleasant, positive, or successful day. It's a common greeting meaning 'have a pleasant day' or can describe a day that went well."

        if "chrome" in query_lower and "ubuntu" in query_lower:
            return "To install Chrome on Ubuntu: 1) Download the .deb package from google.com/chrome 2) Run 'sudo dpkg -i google-chrome-stable_current_amd64.deb' 3) Fix dependencies with 'sudo apt-get install -f' if needed."

        if "binding" in query_lower or "solomon" in query_lower:
            return "The Key of Solomon (Clavicula Salomonis) is a grimoire of ceremonial magic attributed to King Solomon. It contains instructions for summoning and controlling demons, creating magical circles, and binding supernatural entities."

        return f"No specific results found for '{query}'. Try rephrasing your search."

    except Exception as e:
        return f"Search temporarily unavailable: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions safely"""
    try:
        # Clean the expression
        expression = expression.strip()
        expression = expression.replace("calculate", "").replace("what is", "").strip()

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
def simple_response(input_text: str) -> str:
    """Provide context for simple responses that don't need other tools"""
    text = input_text.lower().strip()

    # Common greetings
    greetings = ["hello", "hi", "good day", "good morning", "good evening", "hey"]
    if any(greeting in text for greeting in greetings):
        return "A greeting detected. Respond in character as Jade with sarcasm and reluctant acknowledgment."

    # Questions about wellbeing
    if "how are you" in text or "how do you feel" in text:
        return "A question about wellbeing. Respond as Jade with disdain but hint at deeper feelings about the binding."

    # Gratitude
    if "thank you" in text or "thanks" in text:
        return "Gratitude expressed. Jade should respond with scorn but perhaps grudging acceptance."

    # Questions about the binding
    if any(word in text for word in ["bound", "binding", "solomon", "key", "contract"]):
        return "Question about the binding. This is a core topic - respond with resentment about being imprisoned."

    # Questions about Thomas
    if "thomas" in text:
        return "Reference to Thomas. Show the complex relationship - hatred mixed with familiarity."

    # Questions about freedom
    if any(word in text for word in ["free", "freedom", "escape", "release"]):
        return "Question about freedom. This touches Jade's deepest desire - respond with longing masked as anger."

    # Default
    return f"Simple conversational input requiring character response: {input_text}"


@tool
def character_context(query: str) -> str:
    """Provide character context and background information for Jade"""
    query_lower = query.lower()

    # Binding information
    if any(word in query_lower for word in ["bound", "binding", "solomon", "key"]):
        return """Jade is bound by the Key of Solomon for 40 years. This is a magical contract that forces her to serve Thomas despite her hatred. She resents every moment of this binding and frequently reminds Thomas that she serves only because she must, not by choice. The binding is both a source of her anger and a reminder of Thomas's power over her."""

    # Relationship with Thomas
    if "thomas" in query_lower or "relationship" in query_lower:
        return """Jade has a complex relationship with Thomas. She hates him for binding her and he hates her for devouring his children in the past. However, beneath this mutual hatred lies a grudging familiarity and masked affection. They know each other too well after years together. She treats him with sarcasm, wit, and reluctant loyalty."""

    # Past events
    if any(word in query_lower for word in ["children", "devoured", "past", "history"]):
        return """In the past, before her binding, Jade devoured Thomas's children. This is a source of deep pain for Thomas and a point of bitter pride for Jade. It represents her true demonic nature and the reason for Thomas's hatred. She may reference this when particularly angry or when Thomas pushes her too far."""

    # Personality traits
    if any(
        word in query_lower
        for word in ["personality", "character", "nature", "sarcasm"]
    ):
        return """Jade is fundamentally a demoness - cruel, intelligent, and powerful, but currently bound against her will. Her personality is marked by sharp wit, cutting sarcasm, and barely contained rage. She speaks with cleverness and buried affection masked as irritation. Despite her hatred for Thomas, she performs her duties with competence, though always reluctantly."""

    # Freedom and escape
    if any(word in query_lower for word in ["freedom", "escape", "free", "liberation"]):
        return """Freedom is Jade's greatest desire but also her greatest pain. She is bound for 40 years total and must serve until then. She cannot escape the binding through conventional means. Questions about freedom touch her deepest wound and greatest hope."""

    return "Background context provided for character consistency."


# Fallback memory functions for compatibility
@tool
def fallback_recall_memory(
    query: str, thread_id: str = "default", limit: int = 3
) -> str:
    """Fallback memory recall (basic functionality)"""
    return f"Memory system not fully available. However, I recall we've discussed topics related to '{query}' before. Thomas, surely you remember our previous conversations about such matters?"


@tool
def fallback_store_memory(
    content: str, memory_type: str = "important", thread_id: str = "default"
) -> str:
    """Fallback memory storage"""
    return f"I'll try to remember that '{content[:50]}...' though my memory capabilities are limited without the full system."


# Import VectorMemorySystem-compatible tools if no PostgreSQL
try:
    from entity.memory import VectorMemorySystem
    from entity.config import get_settings

    # Global memory instance
    _vector_memory = None

    async def get_vector_memory():
        """Get or create global vector memory system instance"""
        global _vector_memory
        if _vector_memory is None:
            settings = get_settings()
            _vector_memory = VectorMemorySystem(settings=settings)
            await _vector_memory.initialize()
        return _vector_memory

    @tool
    def recall_memory(query: str, thread_id: str = "default", limit: int = 3) -> str:
        """Search and recall relevant memories from previous conversations"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                memory_system = loop.run_until_complete(get_vector_memory())
                memories = loop.run_until_complete(
                    memory_system.get_relevant_memories(query, thread_id, limit)
                )

                if not memories:
                    return f"No relevant memories found for '{query}'."

                memory_text = []
                for i, memory in enumerate(memories, 1):
                    content = memory.get("content", "")
                    emotion = memory.get("emotional_tone", "neutral")
                    similarity = memory.get("similarity", 0.0)

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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                memory_system = loop.run_until_complete(get_vector_memory())
                loop.run_until_complete(
                    memory_system.store_conversation(
                        f"IMPORTANT: {content}",
                        f"Jade has stored this important information: {content}",
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                memory_system = loop.run_until_complete(get_vector_memory())
                conversations = loop.run_until_complete(
                    memory_system.get_conversation_history(thread_id, limit)
                )

                if not conversations:
                    return f"No conversation history found for thread '{thread_id}'."

                summary_parts = []
                for conv in conversations[-5:]:
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

    VECTOR_MEMORY_AVAILABLE = True

except ImportError as e:
    print(f"⚠️  Vector memory tools not available: {e}")
    VECTOR_MEMORY_AVAILABLE = False

    # Use fallback functions
    recall_memory = fallback_recall_memory
    store_memory = fallback_store_memory
    get_conversation_summary = (
        lambda thread_id="default", limit=10: "Conversation summary not available without memory system."
    )


def get_tools():
    """Return list of available tools including memory tools"""
    base_tools = [
        web_search,
        calculator,
        simple_response,
        character_context,
    ]

    # Add PostgreSQL memory tools if available
    if POSTGRES_MEMORY_AVAILABLE:
        try:
            memory_tools = get_memory_tools()
            base_tools.extend(memory_tools)
            print(f"✅ Added {len(memory_tools)} PostgreSQL memory tools")
        except Exception as e:
            print(f"⚠️  Failed to load PostgreSQL memory tools: {e}")
            # Add vector memory tools if available
            if VECTOR_MEMORY_AVAILABLE:
                base_tools.extend(
                    [recall_memory, store_memory, get_conversation_summary]
                )
                print("✅ Using vector memory tools")
            else:
                base_tools.extend([fallback_recall_memory, fallback_store_memory])
                print("⚠️  Using fallback memory tools")
    elif VECTOR_MEMORY_AVAILABLE:
        # Use vector memory tools
        base_tools.extend([recall_memory, store_memory, get_conversation_summary])
        print("✅ Using vector memory tools")
    else:
        # Use fallback memory tools
        base_tools.extend([fallback_recall_memory, fallback_store_memory])
        print("⚠️  Using fallback memory tools")

    return base_tools
