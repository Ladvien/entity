from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.executor import WorkflowExecutor


class OutputAdapterPlugin(Plugin):
    """Convert workflow responses into external representations."""

    supported_stages = [WorkflowExecutor.OUTPUT]
