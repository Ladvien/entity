from __future__ import annotations

"""Workflow base classes."""

from dataclasses import dataclass, field
from typing import Dict, List

from pipeline.stages import PipelineStage


@dataclass
class Workflow:
    """Mapping of pipeline stages to plugin names."""

    stage_map: Dict[PipelineStage, List[str]] = field(default_factory=dict)

    def get_stage_map(self) -> Dict[PipelineStage, List[str]]:
        """Return mapping of stages to plugin names."""

        return self.stage_map


__all__ = ["Workflow"]
