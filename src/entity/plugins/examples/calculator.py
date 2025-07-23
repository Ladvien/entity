from __future__ import annotations

import ast
import operator
from ..tool import ToolPlugin
from ...workflow.executor import WorkflowExecutor


_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Num):  # type: ignore[attr-defined]
        return node.n
    if isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPS:
            return _ALLOWED_OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


class Calculator(ToolPlugin):
    """Evaluate a simple arithmetic expression."""

    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        expr = context.message or "0"
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree.body)
        return str(result)
