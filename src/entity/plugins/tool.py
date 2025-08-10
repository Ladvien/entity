from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.stages import DO


class ToolPlugin(Plugin):
    """Plugin type for executing external actions."""

    supported_stages = [DO]
    dependencies: list[str] = []
