from __future__ import annotations

import asyncio

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class SlowPlugin(Plugin):
    """Plugin that sleeps for 20 seconds."""

    supported_stages = [WorkflowExecutor.THINK]

    async def _execute_impl(self, context) -> str:
        await asyncio.sleep(20)
        return context.message or ""
