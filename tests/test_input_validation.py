import asyncio

import pytest
<<<<<<< HEAD
=======
from user_plugins.tools.calculator_tool import CalculatorTool
>>>>>>> 9c565435c8c98d3dd664501aa929f40fe2e70c3f

from pipeline.resources.llm_resource import LLMResource
from user_plugins.tools.calculator_tool import CalculatorTool


class EchoLLM(LLMResource):
    async def generate(self, prompt: str) -> str:  # pragma: no cover - simple echo
        self.last_prompt = prompt
        return prompt


@pytest.mark.unit
def test_sql_injection_rejected():
    tool = CalculatorTool()
    with pytest.raises(ValueError):
        asyncio.run(tool.execute_function({"expression": "1; DROP TABLE t"}))


@pytest.mark.unit
def test_xss_prompt_sanitized():
    llm = EchoLLM({})
    result = asyncio.run(llm.call_llm("<script>alert(1)</script>", sanitize=True))
    assert llm.last_prompt == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert result == "&lt;script&gt;alert(1)&lt;/script&gt;"
