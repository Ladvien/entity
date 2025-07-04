import asyncio

import pytest

<<<<<<< HEAD
from plugins.tools.calculator_tool import CalculatorTool
=======
from pipeline.user_plugins.tools.calculator_tool import CalculatorTool
>>>>>>> af319b68dc2109eede14ae624413f7e5304d62df


@pytest.mark.unit
def test_calculator_addition():
    tool = CalculatorTool()
    result = asyncio.run(tool.execute_function({"expression": "2 + 3 * 4"}))
    assert result == 14


@pytest.mark.unit
def test_calculator_invalid_expression():
    tool = CalculatorTool()
    with pytest.raises(ValueError):
        asyncio.run(
            tool.execute_function({"expression": "__import__('os').system('ls')"})
        )
