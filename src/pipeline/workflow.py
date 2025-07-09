from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Iterable, Optional

from entity.core.builder import _AgentBuilder
from entity.core.runtime import _AgentRuntime
from .stages import PipelineStage

WorkflowMapping = Mapping[PipelineStage | str, Iterable[str]]

__all__ = ["Pipeline", "Workflow"]


@dataclass
class Pipeline:
    """Simple pipeline wrapper holding builder and workflow."""

    builder: _AgentBuilder = field(default_factory=_AgentBuilder)
    workflow: Optional[WorkflowMapping] = None

    def build_runtime(self) -> _AgentRuntime:
        """Build an AgentRuntime using the stored builder and workflow."""

        return self.builder.build_runtime(workflow=self.workflow)
