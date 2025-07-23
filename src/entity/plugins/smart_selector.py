from __future__ import annotations

from typing import Any, Iterable

from .prompt import PromptPlugin
from ..tools.registry import ToolInfo
from ..workflow.executor import WorkflowExecutor


class SmartToolSelectorPlugin(PromptPlugin):
    """Select and execute the most relevant tool."""

    stage = WorkflowExecutor.THINK
    dependencies: list[str] = []

    def _rank_tools_by_relevance(
        self, tools: Iterable[ToolInfo], message: str | None
    ) -> ToolInfo | None:
        text = (message or "").lower()
        for tool in tools:
            if tool.name.lower() in text:
                return tool
        return next(iter(tools), None)

    async def _execute_impl(self, context) -> Any:  # noqa: D401
        available = context.discover_tools()
        best = self._rank_tools_by_relevance(available, context.message)
        if best is None:
            return context.message or ""
        result = await context.tool_use(best.name)
        await context.remember("selected_tool", best.name)
        return result
