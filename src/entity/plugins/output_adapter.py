from __future__ import annotations

from typing import Any

from .base import Plugin
from ..workflow.executor import WorkflowExecutor


class OutputAdapterPlugin(Plugin):
    """Convert workflow responses into external representations."""

    supported_stages = [WorkflowExecutor.OUTPUT]
