from __future__ import annotations

"""Error classes that include execution context information."""

from typing import Any, Dict

from ..stages import PipelineStage
from .exceptions import PipelineError


class PipelineContextError(PipelineError):
    """Base error carrying additional context."""

    def __init__(self, message: str, context: Dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context: Dict[str, Any] = context or {}


class StageExecutionError(PipelineContextError):
    """Raised when a pipeline stage fails."""

    def __init__(
        self,
        stage: PipelineStage,
        message: str,
        context: Dict[str, Any] | None = None,
    ) -> None:
        self.stage = stage
        super().__init__(f"{stage.name} stage failed: {message}", context)


class PluginContextError(StageExecutionError):
    """Raised when a plugin within a stage fails."""

    def __init__(
        self,
        stage: PipelineStage,
        plugin_name: str,
        message: str,
        context: Dict[str, Any] | None = None,
    ) -> None:
        self.plugin_name = plugin_name
        super().__init__(stage, f"Plugin '{plugin_name}' error: {message}", context)
