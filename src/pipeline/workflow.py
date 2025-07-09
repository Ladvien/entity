from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Iterable, Optional

from entity.core.builder import AgentBuilder
from entity.core.runtime import AgentRuntime
from .stages import PipelineStage

WorkflowMapping = Mapping[PipelineStage | str, Iterable[str]]


@dataclass
class Pipeline:
    """Simple pipeline wrapper holding builder and workflow."""

    builder: AgentBuilder = field(default_factory=AgentBuilder)
    workflow: Optional[WorkflowMapping] = None

    def build_runtime(self) -> AgentRuntime:
        """Build an AgentRuntime using the stored builder and workflow."""

        return self.builder.build_runtime(workflow=self.workflow)
