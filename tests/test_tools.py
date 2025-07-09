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


def test_tool_retry_success():
    tool = FailOnceTool({"max_retries": 1, "retry_delay": 0})
    result = asyncio.run(tool.execute_function_with_retry({"text": "hi"}))
    assert result == "hi"
    assert tool.calls == 2


def test_tool_retry_exceeds():
    tool = FailOnceTool({"max_retries": 0, "retry_delay": 0})
    with pytest.raises(RuntimeError):
        asyncio.run(tool.execute_function_with_retry({"text": "hi"}))
    assert tool.calls == 1
