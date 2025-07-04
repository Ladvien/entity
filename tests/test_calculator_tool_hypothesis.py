import asyncio

from hypothesis import given
from hypothesis import strategies as st

from plugins.tools.calculator_tool import CalculatorTool


def _eval(expr: str) -> int | float:
    return eval(expr)


@st.composite
def arithmetic_expr(draw):
    a = draw(st.integers(-10, 10))
    op = draw(st.sampled_from(["+", "-", "*", "/"]))
    if op == "/":
        b = draw(st.integers(-10, 10).filter(lambda x: x != 0))
    else:
        b = draw(st.integers(-10, 10))
    expr = f"{a} {op} {b}"
    return expr, _eval(expr)


@given(arithmetic_expr())
def test_calculator_arithmetic(expr_result):
    expr, expected = expr_result
    result = asyncio.run(CalculatorTool().execute_function({"expression": expr}))
    assert result == expected
