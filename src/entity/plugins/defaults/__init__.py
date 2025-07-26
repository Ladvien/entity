from __future__ import annotations

from typing import Any

from entity.plugins.base import Plugin
from entity.cli.ent_cli_adapter import EntCLIAdapter
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.workflow import Workflow


class InputPlugin(Plugin):
    supported_stages = [WorkflowExecutor.INPUT]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return input unchanged."""
        return context.message or ""


class ParsePlugin(Plugin):
    supported_stages = [WorkflowExecutor.PARSE]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class ThinkPlugin(Plugin):
    supported_stages = [WorkflowExecutor.THINK]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class DoPlugin(Plugin):
    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class ReviewPlugin(Plugin):
    supported_stages = [WorkflowExecutor.REVIEW]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class OutputPlugin(Plugin):
    supported_stages = [WorkflowExecutor.OUTPUT]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return final response and terminate the workflow."""

        message = context.message or ""
        context.say(message)
        return message


def default_workflow(resources: dict[str, Any]) -> Workflow:
    """Return the built-in workflow with one plugin per stage."""

    steps = {
        WorkflowExecutor.INPUT: [EntCLIAdapter(resources)],
        WorkflowExecutor.PARSE: [ParsePlugin(resources)],
        WorkflowExecutor.THINK: [ThinkPlugin(resources)],
        WorkflowExecutor.DO: [DoPlugin(resources)],
        WorkflowExecutor.REVIEW: [ReviewPlugin(resources)],
        WorkflowExecutor.OUTPUT: [EntCLIAdapter(resources)],
    }
    return Workflow(steps, WorkflowExecutor._STAGES)
