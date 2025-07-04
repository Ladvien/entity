import asyncio

import pytest

from plugins.tools.calculator_tool import CalculatorTool


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
