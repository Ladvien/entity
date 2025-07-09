from __future__ import annotations

"""Simplified plugin base classes used inside ``entity.core``.

These wrappers mirror the core architecture described in
``architecture/general.md`` while delegating heavy lifting to the
implementations under ``pipeline.base_plugins``. The goal is to expose a
clean, easy to understand interface for plugin authors.
"""

from typing import Any, List

from pipeline.base_plugins import (
    AdapterPlugin as _AdapterPlugin,
    BasePlugin as _BasePlugin,
    FailurePlugin as _FailurePlugin,
    PromptPlugin as _PromptPlugin,
    ResourcePlugin as _ResourcePlugin,
    ToolPlugin as _ToolPlugin,
)
from pipeline.stages import PipelineStage


class BasePlugin(_BasePlugin):
    """Foundation for all plugins."""

    # Default behaviour described in the architecture document
    stages: List[PipelineStage]
    dependencies: List[str] = []
    failure_threshold: int = 3
    failure_reset_timeout: float = 60.0
    max_retries: int = 1
    retry_delay: float = 0.0

    async def _execute_impl(self, context: Any) -> Any:
        """Execute plugin logic in the pipeline."""
        raise NotImplementedError


class ResourcePlugin(_ResourcePlugin):
    """Infrastructure plugin providing persistent resources."""


class ToolPlugin(_ToolPlugin):
    """Utility plugin executed via ``tool_use`` calls."""


class PromptPlugin(_PromptPlugin):
    """Processing plugin typically run in ``THINK`` stage."""

    stages = [PipelineStage.THINK]


class AdapterPlugin(_AdapterPlugin):
    """Input or output adapter plugin."""

    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]


class FailurePlugin(_FailurePlugin):
    """Error handling plugin for the ``ERROR`` stage."""

    stages = [PipelineStage.ERROR]
