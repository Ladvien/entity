from .fun_fact_tool import FunFactTool
from .memory_tools import MemorySearchTool, StoreMemoryTool, MemorySearchInput, StoreMemoryInput

PLUGIN_TOOLS = [
    StoreMemoryTool,
    MemorySearchTool,
    FunFactTool,
]

__all__ = [
    'FunFactTool',
    'MemorySearchTool',
    'StoreMemoryTool',
    'MemorySearchInput',
    'StoreMemoryInput',
]
