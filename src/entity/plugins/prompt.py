from __future__ import annotations

from typing import Any

from .base import Plugin
from ..workflow.executor import WorkflowExecutor


class PromptPlugin(Plugin):
    """LLM-driven reasoning or validation plugin."""

    supported_stages = [WorkflowExecutor.THINK, WorkflowExecutor.REVIEW]
    dependencies: list[str] = ["llm"]
