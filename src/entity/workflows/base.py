from __future__ import annotations

"""Workflow definitions for pipeline execution."""

from typing import ClassVar, Dict, Iterable, List, Mapping

from pydantic import BaseModel, Field

from entity.pipeline.stages import PipelineStage


class Workflow(BaseModel):
    """Reusable mapping from :class:`PipelineStage` to plugin names."""

    stage_map: ClassVar[Dict[PipelineStage | str, Iterable[str]]] = {}
    stages: Dict[PipelineStage, List[str]] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        mapping: Mapping[PipelineStage | str, Iterable[str]] | None = None,
        **params: str,
    ) -> None:
        values = {}
        mapping = mapping or self.stage_map
        processed: Dict[PipelineStage, List[str]] = {}
        for stage, plugins in mapping.items():
            formatted = [str(p).format(**params) for p in plugins]
            self._assign_to(processed, stage, formatted)
        values["stages"] = processed
        super().__init__(**values)

    @staticmethod
    def _assign_to(
        dest: Dict[PipelineStage, List[str]],
        stage: PipelineStage | str,
        plugins: Iterable[str],
    ) -> None:
        stage_obj = PipelineStage.ensure(stage)
        names = [str(p) for p in plugins]
        if not all(names):
            raise ValueError("Plugin names must be non-empty strings")
        dest[stage_obj] = names

    def _assign(self, stage: PipelineStage | str, plugins: Iterable[str]) -> None:
        self._assign_to(self.stages, stage, plugins)

    def to_dict(self) -> Dict[str, List[str]]:
        return {str(stage).lower(): list(names) for stage, names in self.stages.items()}

    def copy(self, **params: str) -> "Workflow":
        """Return a new workflow with updated parameters."""
        return self.__class__(mapping=self.stages, **params)

    @classmethod
    def from_dict(cls, data: Dict[str, Iterable[str]]) -> "Workflow":
        mapping = {PipelineStage.ensure(k): list(v) for k, v in data.items()}
        return cls(mapping)
