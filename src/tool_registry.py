from typing import Callable, List, Dict, Any
from langchain_core.tools import tool
from src.memory import VectorMemorySystem

from langchain_core.tools import tool
from typing import Dict, Any, Callable
from langchain_core.tools import BaseTool  # Base class for tools


class ToolRegistry:
    def __init__(self):
        self._tools: List[Callable] = []
        self._context: Dict[str, Any] = {}

    def set_context(self, context: Dict[str, Any]):
        self._context = context

    def register(self, fn: Callable):
        """Register a static tool function."""
        self._tools.append(tool(fn))
        return fn

    def register_factory(self, factory: Callable):
        tool_fn = factory(self._context)

        if isinstance(tool_fn, BaseTool):
            self._tools.append(tool_fn)  # already a valid tool
        else:
            self._tools.append(tool(tool_fn))  # raw function, decorate it

        return tool_fn

    def get_tools(self) -> List[Callable]:
        return self._tools


def register_memory_tools(context: Dict[str, Any]) -> Callable:
    """
    Factory function that returns a tool function using the initialized memory system.
    """
    memory: VectorMemorySystem = context["memory"]

    @tool
    async def search_memory_tool(query: str, thread_id: str = "") -> str:
        """
        Search the memory database for relevant entries.
        """
        results = await memory.search_memory(query, thread_id=thread_id)
        return "\n\n".join([doc.page_content for doc in results])

    return search_memory_tool
