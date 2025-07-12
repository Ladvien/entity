import asyncio

import pytest
from entity.core.plugins import ToolPlugin


class FailOnceTool(ToolPlugin):
    required_params = ["text"]

    def __init__(self, config=None):
        super().__init__(config)
        self.calls = 0

    async def execute_function(self, params):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("fail")
        return params["text"]


def test_tool_exception_propagates_without_retry():
    tool = FailOnceTool({})
    with pytest.raises(RuntimeError):
        asyncio.run(tool.execute_function_with_retry({"text": "hi"}))
    assert tool.calls == 1
