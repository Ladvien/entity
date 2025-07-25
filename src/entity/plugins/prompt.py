from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class PromptPlugin(Plugin):
    """LLM-driven reasoning or validation plugin."""

    supported_stages = [WorkflowExecutor.THINK, WorkflowExecutor.REVIEW]
    dependencies: list[str] = ["llm"]
