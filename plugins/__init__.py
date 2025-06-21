# plugins/__init__.py

from plugins.memory_tools import StoreMemoryTool, MemorySearchTool, DeepMemorySearchTool
from plugins.fun_fact_tool import FunFactTool

PLUGIN_TOOLS = [
    StoreMemoryTool,
    MemorySearchTool,
    DeepMemorySearchTool,
    FunFactTool,
]
