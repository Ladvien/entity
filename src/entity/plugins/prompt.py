from __future__ import annotations

from typing import Any

from .base import Plugin
from ..workflow.executor import WorkflowExecutor


class PromptPlugin(Plugin):
    """LLM-driven reasoning or validation plugin."""

    supported_stages = [WorkflowExecutor.THINK, WorkflowExecutor.REVIEW]
    dependencies: list[str] = ["llm"]

    def _enforce_stage(self, context: Any) -> None:  # noqa: D401
        """Ensure plugin executes only in supported stages."""
        super()._enforce_stage(context)
        current = getattr(context, "current_stage", None)
        if current not in self.supported_stages:
            raise RuntimeError(
                f"{self.__class__.__name__} cannot run in stage '{current}'"
            )
