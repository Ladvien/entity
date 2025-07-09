from __future__ import annotations

"""Simple workflow representation mapping stages to plugin names."""

from dataclasses import dataclass, field
from typing import Dict, List

from .stages import PipelineStage


@dataclass
class Workflow:
    """Mapping of :class:`PipelineStage` to plugin names."""

    stage_map: Dict[PipelineStage, List[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]] | None) -> "Workflow":
        stage_map: Dict[PipelineStage, List[str]] = {}
        if data:
            for stage, plugins in data.items():
                stage_obj = PipelineStage.ensure(stage)
                if not isinstance(plugins, list):
                    raise ValueError(f"Workflow stage '{stage}' must be a list")
                stage_map[stage_obj] = list(plugins)
        return cls(stage_map)

    def get(self, stage: PipelineStage) -> List[str]:
        return self.stage_map.get(stage, [])
