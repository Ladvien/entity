from __future__ import annotations

from entity.plugins.base import Plugin
from entity.workflow.stages import OUTPUT


class OutputAdapterPlugin(Plugin):
    """Convert workflow responses into external representations."""

    supported_stages = [OUTPUT]
