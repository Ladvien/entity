from __future__ import annotations

"""Workflow definitions for pipeline execution."""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from pipeline.stages import PipelineStage


@dataclass
class Workflow:
    """Map :class:`PipelineStage` to plugin names."""

    stages: Dict[PipelineStage, List[str]] = field(default_factory=dict)

    def __init__(
        self, mapping: Dict[PipelineStage | str, Iterable[str]] | None = None
    ) -> None:
        self.stages = {}
        if mapping:
            for stage, plugins in mapping.items():
                self._assign(stage, plugins)

    def _assign(self, stage: PipelineStage | str, plugins: Iterable[str]) -> None:
        stage_obj = PipelineStage.ensure(stage)
        names = [str(p) for p in plugins]
        if not all(names):
            raise ValueError("Plugin names must be non-empty strings")
        self.stages[stage_obj] = names

    def to_dict(self) -> Dict[str, List[str]]:
        return {str(stage).lower(): list(names) for stage, names in self.stages.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Iterable[str]]) -> "Workflow":
        mapping = {PipelineStage.ensure(k): list(v) for k, v in data.items()}
        return cls(mapping)
