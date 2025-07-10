from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional

from entity.core.builder import _AgentBuilder
from entity.core.runtime import AgentRuntime
from entity.workflows.base import Workflow as BaseWorkflow

from .stages import PipelineStage

WorkflowMapping = Mapping[PipelineStage | str, Iterable[str]]

Workflow = BaseWorkflow

__all__ = ["Pipeline", "Workflow"]


@dataclass
class Pipeline:
    """Simple pipeline wrapper holding builder and workflow."""

    builder: _AgentBuilder = field(default_factory=_AgentBuilder)
    workflow: Optional[WorkflowMapping] = None

    def build_runtime(self) -> AgentRuntime:
        """Build an AgentRuntime using the stored builder and workflow."""

        return self.builder.build_runtime(workflow=self.workflow)


@dataclass
class Workflow:
    """Mapping of pipeline stages to plugin names."""

    stage_map: WorkflowMapping

    @classmethod
    def from_dict(cls, data: Mapping[str, Iterable[str]]) -> "Workflow":
        mapping: dict[PipelineStage, list[str]] = {}
        for stage, plugins in data.items():
            stage_enum = PipelineStage.ensure(stage)
            names = list(plugins)
            mapping[stage_enum] = [str(p) for p in names]
        return cls(mapping)
