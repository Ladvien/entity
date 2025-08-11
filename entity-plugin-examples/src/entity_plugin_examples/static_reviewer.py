from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class StaticReviewer(Plugin):
    """Pass-through REVIEW stage plugin."""

    supported_stages = [WorkflowExecutor.REVIEW]

    async def _execute_impl(self, context) -> str:
        return context.message or ""
