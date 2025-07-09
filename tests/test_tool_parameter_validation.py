import asyncio

import pytest
from pipeline.base_plugins import ToolPlugin
from pipeline.errors import ToolExecutionError
from pydantic import BaseModel

from user_plugins.tools.search_tool import SearchTool


class EchoTool(ToolPlugin):
    class Params(BaseModel):
        text: str

    async def execute_function(self, params: Params):
        return params.text


async def run(tool, params):
    return await tool.execute_function_with_retry(params)


def test_builtin_tool_invalid_params():
    tool = SearchTool()
    with pytest.raises(ToolExecutionError):
        asyncio.run(run(tool, {}))


def test_custom_tool_param_validation():
    tool = EchoTool({})
    result = asyncio.run(run(tool, {"text": "hi"}))
    assert result == "hi"


def test_custom_tool_invalid_param():
    tool = EchoTool({})
    with pytest.raises(ToolExecutionError):
        asyncio.run(run(tool, {}))
