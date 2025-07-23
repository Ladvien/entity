from __future__ import annotations

from typing import Any

from .base import Plugin
from ..workflow.executor import WorkflowExecutor


class InputAdapterPlugin(Plugin):
    """Convert external input into workflow messages."""

    supported_stages = [WorkflowExecutor.INPUT]
