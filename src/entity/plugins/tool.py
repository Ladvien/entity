from __future__ import annotations

from typing import Any

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class ToolPlugin(Plugin):
    """Plugin type for executing external actions."""

    supported_stages = [WorkflowExecutor.DO]
    dependencies: list[str] = []
