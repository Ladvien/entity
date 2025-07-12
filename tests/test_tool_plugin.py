import asyncio

import pytest
from entity.core.plugins import ToolPlugin
from pipeline.errors import ToolExecutionError


class EchoTool(ToolPlugin):
    required_params = ["text"]

    async def execute_function(self, params):
        return params["text"]


async def run_tool(tool, params):
    return await tool.execute_function_with_retry(params)


def test_tool_plugin_valid_params():
    tool = EchoTool({})
    result = asyncio.run(run_tool(tool, {"text": "hi"}))
    assert result == "hi"


def test_tool_plugin_missing_param():
    tool = EchoTool({})
    with pytest.raises(ToolExecutionError):
        asyncio.run(run_tool(tool, {}))
