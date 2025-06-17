from typing import Callable, List, Dict, Any
from langchain_core.tools import tool

class ToolRegistry:
    def __init__(self):
        self._tools: List[Callable] = []
        self._context: Dict[str, Any] = {}

    def set_context(self, context: Dict[str, Any]):
        self._context = context

    def register(self, fn: Callable):
        self._tools.append(tool(fn))
        return fn

    def register_factory(self, factory: Callable):
        tool_fn = factory(self._context)
        self._tools.append(tool(tool_fn))
        return tool_fn

    def get_tools(self) -> List[Callable]:
        return self._tools

tool_registry = ToolRegistry()
