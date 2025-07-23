from __future__ import annotations

import sys
from typing import Any

from ..plugins.input_adapter import InputAdapterPlugin
from ..plugins.output_adapter import OutputAdapterPlugin
from ..workflow.executor import WorkflowExecutor
from ..plugins.context import PluginContext


class EntCLIAdapter(InputAdapterPlugin, OutputAdapterPlugin):
    """Simple CLI adapter using stdin and stdout."""

    supported_stages = [WorkflowExecutor.INPUT, WorkflowExecutor.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> str:
        if context.current_stage == WorkflowExecutor.INPUT:
            message = sys.stdin.readline().rstrip("\n")
            await context.remember("cli_input", message)
            return message
        if context.current_stage == WorkflowExecutor.OUTPUT:
            output = context.message or ""
            print(output)
            context.say(output)
            return output
        return context.message or ""
