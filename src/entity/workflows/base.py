from __future__ import annotations

"""Workflow definitions for pipeline execution."""

from typing import Callable, ClassVar, Dict, Iterable, List, Mapping

from pydantic import BaseModel, Field

from entity.pipeline.stages import PipelineStage


from entity.pipeline.state import PipelineState


class Workflow(BaseModel):
    """Reusable mapping from :class:`PipelineStage` to plugin names."""

    stage_map: ClassVar[Dict[PipelineStage | str, Iterable[str]]] = {}
    stage_conditions: ClassVar[
        Dict[PipelineStage | str, Callable[[PipelineState], bool]]
    ] = {}

    stages: Dict[PipelineStage, List[str]] = Field(default_factory=dict)
    conditions: Dict[PipelineStage, Callable[[PipelineState], bool]] = Field(
        default_factory=dict
    )

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        mapping: Mapping[PipelineStage | str, Iterable[str]] | None = None,
        conditions: (
            Mapping[PipelineStage | str, Callable[[PipelineState], bool]] | None
        ) = None,
        **params: str,
    ) -> None:
        values = {}
        mapping = mapping or self.combined_stage_map()
        conditions = conditions or self.combined_conditions()
        processed: Dict[PipelineStage, List[str]] = {}
        for stage, plugins in mapping.items():
            formatted = [str(p).format(**params) for p in plugins]
            self._assign_to(processed, stage, formatted)
        cond_map: Dict[PipelineStage, Callable[[PipelineState], bool]] = {}
        for stage, cond in conditions.items():
            cond_map[PipelineStage.ensure(stage)] = cond
        values["stages"] = processed
        values["conditions"] = cond_map
        super().__init__(**values)

    # ------------------------------------------------------------------
    # Composition helpers
    # ------------------------------------------------------------------

    @classmethod
    def combined_stage_map(cls) -> Dict[PipelineStage | str, Iterable[str]]:
        mapping: Dict[PipelineStage | str, Iterable[str]] = {}
        for base in reversed(cls.__mro__):
            if issubclass(base, Workflow) and hasattr(base, "stage_map"):
                mapping.update(getattr(base, "stage_map", {}))
        return mapping

    @classmethod
    def combined_conditions(
        cls,
    ) -> Dict[PipelineStage | str, Callable[[PipelineState], bool]]:
        combined: Dict[PipelineStage | str, Callable[[PipelineState], bool]] = {}
        for base in reversed(cls.__mro__):
            if issubclass(base, Workflow) and hasattr(base, "stage_conditions"):
                combined.update(getattr(base, "stage_conditions", {}))
        return combined

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    def should_execute(self, stage: PipelineStage, state: PipelineState) -> bool:
        condition = self.conditions.get(stage)
        if condition is not None:
            return bool(condition(state))
        return True

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
