from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.executor import WorkflowExecutor


class InputAdapterPlugin(Plugin):
    """Convert external input into workflow messages."""

    supported_stages = [WorkflowExecutor.INPUT]
