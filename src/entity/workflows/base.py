from __future__ import annotations

"""Workflow definitions for pipeline execution."""

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Iterable, List

from pipeline.stages import PipelineStage


@dataclass
class Workflow:
    """Reusable mapping from :class:`PipelineStage` to plugin names."""

    stage_map: ClassVar[Dict[PipelineStage | str, Iterable[str]]] = {}
    stages: Dict[PipelineStage, List[str]] = field(default_factory=dict)

    def __init__(
        self,
        mapping: Dict[PipelineStage | str, Iterable[str]] | None = None,
        **params: str,
    ) -> None:
        self.stages = {}
        mapping = mapping or self.stage_map
        for stage, plugins in (mapping or {}).items():
            formatted = [str(p).format(**params) for p in plugins]
            self._assign(stage, formatted)

    def _assign(self, stage: PipelineStage | str, plugins: Iterable[str]) -> None:
        stage_obj = PipelineStage.ensure(stage)
        names = [str(p) for p in plugins]
        if not all(names):
            raise ValueError("Plugin names must be non-empty strings")
        self.stages[stage_obj] = names

    def to_dict(self) -> Dict[str, List[str]]:
        return {str(stage).lower(): list(names) for stage, names in self.stages.items()}

    def copy(self, **params: str) -> "Workflow":
        """Return a new workflow with updated parameters."""
        return self.__class__(mapping=self.stages, **params)

    @classmethod
    def from_dict(cls, data: Dict[str, Iterable[str]]) -> "Workflow":
        mapping = {PipelineStage.ensure(k): list(v) for k, v in data.items()}
        return cls(mapping)
