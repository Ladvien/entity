from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional

from typing import TYPE_CHECKING

from entity.core.agent import _AgentBuilder

if TYPE_CHECKING:
    from entity.core.agent import AgentRuntime
else:
    AgentRuntime = object  # type: ignore
from entity.workflows.base import Workflow

from .stages import PipelineStage

WorkflowMapping = Mapping[PipelineStage | str, Iterable[str]]

__all__ = ["Pipeline", "Workflow"]


@dataclass
class Pipeline:
    """Simple pipeline wrapper holding builder and workflow."""

    builder: _AgentBuilder = field(default_factory=_AgentBuilder)
    workflow: Optional[WorkflowMapping] = None

    async def build_runtime(self) -> AgentRuntime:
        """Build an AgentRuntime using the stored builder and workflow."""

        return await self.builder.build_runtime(workflow=self.workflow)
