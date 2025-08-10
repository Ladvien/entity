from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.stages import INPUT


class InputAdapterPlugin(Plugin):
    """Convert external input into workflow messages."""

    supported_stages = [INPUT]
