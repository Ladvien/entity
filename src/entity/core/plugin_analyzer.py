from __future__ import annotations

"""Utilities for inspecting plugin functions."""

from typing import Callable
import ast
import inspect
import textwrap


def suggest_upgrade(func: Callable) -> str | None:
    """Return a suggestion to upgrade ``func`` to a class plugin if complex."""
    try:
        source = inspect.getsource(func)
    except OSError:
        return None

    lines = len(source.splitlines())
    if lines > 20:
        return f"Function '{func.__name__}' is {lines} lines long; consider a class-based plugin for clarity."

    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return None

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.complex = False

        def visit_For(self, node: ast.For) -> None:  # type: ignore[override]
            self.complex = True

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:  # type: ignore[override]
            self.complex = True

        def visit_While(self, node: ast.While) -> None:  # type: ignore[override]
            self.complex = True

        def visit_If(self, node: ast.If) -> None:  # type: ignore[override]
            if node.orelse:
                self.complex = True
            self.generic_visit(node)

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    if visitor.complex:
        return f"Function '{func.__name__}' contains loops or branches; consider upgrading to a class."

    return None
