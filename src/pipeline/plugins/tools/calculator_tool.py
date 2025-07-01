from __future__ import annotations

import ast
from typing import Any, Dict

from pipeline.base_plugins import ToolPlugin
from pipeline.stages import PipelineStage


class SafeEvaluator:
    """Safely evaluate a simple arithmetic expression."""

    _ALLOWED_NODES = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Num,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.UAdd,
        ast.USub,
    )

    def evaluate(self, expression: str) -> Any:
        """Evaluate the expression after validating allowed nodes."""
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - invalid path
            raise ValueError(f"Invalid expression: {exc}") from exc

        for node in ast.walk(tree):
            if not isinstance(node, self._ALLOWED_NODES):
                raise ValueError(
                    f"Invalid expression: disallowed node {node.__class__.__name__}"
                )

        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left**right
            raise ValueError("Unsupported binary operator")
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("Unsupported unary operator")
        if isinstance(node, ast.Num):
            return node.n
        raise ValueError("Invalid expression")


class CalculatorTool(ToolPlugin):
    """Evaluate simple math expressions using a safe evaluator.

    Supports **Immediate Tool Access (24)** for quick calculations within
    any stage.
    """

    stages = [PipelineStage.DO]
    _evaluator = SafeEvaluator()

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        expression = params.get("expression")
        if not expression:
            raise ValueError("'expression' parameter is required")
        try:
            return self._evaluator.evaluate(str(expression))
        except Exception as exc:  # noqa: BLE001 - re-raising user error
            raise ValueError(f"Invalid expression: {exc}") from exc
