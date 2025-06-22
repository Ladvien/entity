import pytest
from plugins.memory_tools import (
    MemorySearchInput,
    MemorySearchTool,
    StoreMemoryInput,
    StoreMemoryTool,
)
from src.core.config import ToolConfig
from src.tools.base_tool_plugin import BaseToolPlugin
from src.tools.tools import ToolManager


# Create ToolManager instance with real tools and configuration
@pytest.fixture
def tool_manager_with_config():
    tool_config = ToolConfig(
        enabled=[
            {"name": "memory_search", "max_uses": 2},
            {"name": "store_memory", "max_uses": 1, "max_total": 3},
        ]
    )
    tool_manager = ToolManager(config=tool_config)

    # Register the real tool classes
    tool_manager.register_class(MemorySearchTool)
    tool_manager.register_class(StoreMemoryTool)

    return tool_manager


# Test for MemorySearchTool
@pytest.mark.asyncio
async def test_memory_search_tool(tool_manager_with_config):
    tool = tool_manager_with_config.get_tool("memory_search")

    input_data = MemorySearchInput(query="search query", limit=3)
    result = await tool.run(input_data)

    assert result == "Search results for: search query"


# Test for StoreMemoryTool
@pytest.mark.asyncio
async def test_store_memory_tool(tool_manager_with_config):
    tool = tool_manager_with_config.get_tool("store_memory")

    input_data = StoreMemoryInput(content="Memory content", importance_score=0.8)
    result = await tool.run(input_data)

    assert result == "Memory stored with importance: 0.80"
