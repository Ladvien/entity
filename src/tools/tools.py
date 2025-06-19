# entity_service/tools.py
"""
Tool system with memory integration
"""
import logging
from typing import Dict, Any, List, Optional, Callable
import asyncio

from langchain_core.tools import tool

from memory import VectorMemorySystem

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Tool registry with memory context"""

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._langchain_tools: List[Any] = []
        self.memory_system: Optional[VectorMemorySystem] = None

    def set_memory_system(self, memory_system: VectorMemorySystem):
        """Set the memory system for tools that need it"""
        self.memory_system = memory_system

    def register(self, tool_func: Callable, name: Optional[str] = None):
        """Register a tool function"""
        lc_tool = tool(tool_func)
        tool_name = name or lc_tool.name

        self._tools[tool_name] = lc_tool
        self._langchain_tools.append(lc_tool)

        logger.info(f"Registered tool: {tool_name}")

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a specific tool"""
        return self._tools.get(name)

    def get_all_tools(self) -> List[Any]:
        """Get all tools for LangChain"""
        return self._langchain_tools

    def list_tool_names(self) -> List[str]:
        """List all tool names"""
        return list(self._tools.keys())


async def setup_tools(
    config: Dict[str, Any], memory_system: VectorMemorySystem
) -> ToolRegistry:
    """Setup and register all tools"""
    registry = ToolRegistry()
    registry.set_memory_system(memory_system)

    # Register built-in tools
    if "web_search" in config.get("enabled", []):
        registry.register(web_search_tool)

    if "calculator" in config.get("enabled", []):
        registry.register(calculator_tool)

    if "memory_search" in config.get("enabled", []):
        # Create memory-aware tools
        @tool
        async def search_memories(query: str, thread_id: str = "default") -> str:
            """Search through stored memories"""
            if registry.memory_system:
                memories = await registry.memory_system.search_memory(
                    query, thread_id, k=5
                )
                if memories:
                    return "\n\n".join(
                        [f"Memory: {doc.page_content}" for doc in memories]
                    )
                return "No relevant memories found."
            return "Memory system not available."

        registry.register(search_memories)

    if "store_memory" in config.get("enabled", []):

        @tool
        async def store_important_memory(content: str, importance: float = 0.8) -> str:
            """Store an important piece of information in memory"""
            if registry.memory_system:
                await registry.memory_system.add_memory(
                    thread_id="default",
                    content=content,
                    memory_type="important",
                    importance_score=importance,
                    emotional_tone="neutral",
                )
                return f"Stored in memory: {content[:100]}..."
            return "Memory system not available."

        registry.register(store_important_memory)

    return registry


# Tool implementations
async def web_search_tool(query: str) -> str:
    """Search the web for information"""
    # Simple mock implementation - replace with actual API
    return f"Web search results for '{query}': No results found (mock implementation)"


async def calculator_tool(expression: str) -> str:
    """Calculate mathematical expressions"""
    try:
        # Safe evaluation using ast
        import ast
        import operator

        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Constant):
                return node.value
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
        return f"Cannot calculate '{expression}': {str(e)}"
