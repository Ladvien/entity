from __future__ import annotations

"""Lightweight workflow definition utilities."""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .stages import PipelineStage


@dataclass
class Workflow:
    """Mapping of pipeline stages to plugin names."""

    stages: Dict[PipelineStage, List[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str | PipelineStage, Iterable[str]]) -> "Workflow":
        mapping: Dict[PipelineStage, List[str]] = {}
        for stage, plugins in (data or {}).items():
            stage_obj = PipelineStage.ensure(stage)
            if not isinstance(plugins, Iterable):
                raise ValueError("Workflow stage values must be iterables")
            mapping[stage_obj] = list(plugins)
        return cls(mapping)

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            stage.name.lower(): list(plugins) for stage, plugins in self.stages.items()
        }

    def __iter__(self):  # pragma: no cover - passthrough
        return iter(self.stages.items())
