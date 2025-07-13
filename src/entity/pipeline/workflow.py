from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from entity.core.agent import AgentRuntime, _AgentBuilder
else:
    AgentRuntime = object  # type: ignore

from entity.workflows.base import Workflow


def _builder_factory() -> "_AgentBuilder":
    from entity.core.agent import _AgentBuilder

    return _AgentBuilder()


from .stages import PipelineStage

WorkflowMapping = Mapping[PipelineStage | str, Iterable[str]]

__all__ = ["Pipeline", "Workflow"]


@dataclass
class Pipeline:
    """Simple pipeline wrapper holding builder and workflow."""

    builder: "_AgentBuilder" = field(default_factory=_builder_factory)
    workflow: Optional[Union[Workflow, WorkflowMapping]] = None

    def __post_init__(self) -> None:
        """Validate workflow plugins using the builder's registry."""
        if self.workflow is None:
            return

        wf_obj = (
            self.workflow
            if isinstance(self.workflow, Workflow)
            else Workflow.from_dict(self.workflow)
        )

        for stage, plugins in wf_obj.stages.items():
            for name in plugins:
                if not self.builder.plugin_registry.has_plugin(name):
                    available = []
                    if hasattr(self.builder.plugin_registry, "list_plugins"):
                        available = self.builder.plugin_registry.list_plugins()
                    raise KeyError(
                        f"Plugin '{name}' referenced in stage '{stage}' is not registered. Available plugins: {available}"
                    )

        self.workflow = wf_obj

    async def build_runtime(self) -> AgentRuntime:
        """Build an AgentRuntime using the stored builder and workflow."""
        wf_obj = (
            self.workflow
            if isinstance(self.workflow, Workflow)
            else (
                Workflow.from_dict(self.workflow) if self.workflow is not None else None
            )
        )
        return await self.builder.build_runtime(workflow=wf_obj)
