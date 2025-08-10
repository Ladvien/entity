from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.stages import REVIEW, THINK


class PromptPlugin(Plugin):
    """LLM-driven reasoning or validation plugin."""

    supported_stages = [THINK, REVIEW]
    dependencies: list[str] = ["llm"]
