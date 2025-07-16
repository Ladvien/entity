from __future__ import annotations

"""Workflow definitions for pipeline execution."""

from typing import Any, ClassVar, Dict, Iterable, List, Mapping, Protocol


class _HasPlugin(Protocol):
    def has_plugin(self, name: str) -> bool: ...

    def list_plugins(self) -> List[str]: ...


from pydantic import BaseModel, Field

from entity.pipeline.stages import PipelineStage


from entity.pipeline.state import PipelineState


class Workflow(BaseModel):
    """Reusable mapping from :class:`PipelineStage` to plugin names."""

    stage_map: ClassVar[Dict[PipelineStage | str, Iterable[str]]] = {}
    parent: ClassVar[type["Workflow"] | None] = None

    stages: Dict[PipelineStage, List[str]] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        mapping: Mapping[PipelineStage | str, Iterable[str]] | None = None,
        registry: _HasPlugin | None = None,
        **params: str,
    ) -> None:
        mapping = mapping or self.combined_stage_map()
        processed: Dict[PipelineStage, List[str]] = {}
        for stage, plugins in mapping.items():
            formatted = [str(p).format(**params) for p in plugins]
            self._assign_to(processed, stage, formatted)
        super().__init__(stages=processed)
        object.__setattr__(self, "stage_map", processed)
        if registry is not None:
            self.validate_plugins(registry)

    # ------------------------------------------------------------------
    # Composition helpers
    # ------------------------------------------------------------------

    @classmethod
    def combined_stage_map(cls) -> Dict[PipelineStage | str, Iterable[str]]:
        mapping: Dict[PipelineStage | str, Iterable[str]] = {}
        if cls.parent is not None:
            mapping.update(cls.parent.combined_stage_map())
        for base in reversed(cls.__mro__):
            if issubclass(base, Workflow) and hasattr(base, "stage_map"):
                mapping.update(getattr(base, "stage_map", {}))
        return mapping

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    def should_execute(self, stage: PipelineStage, state: PipelineState) -> bool:
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
    def from_dict(
        cls, data: Mapping[str, Iterable[str]] | Mapping[str, Any]
    ) -> "Workflow":
        mapping = data
        if "stages" in data:
            mapping = data["stages"]  # type: ignore[assignment]
        mapping = {PipelineStage.ensure(k): list(v) for k, v in mapping.items()}
        return cls(mapping)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def validate_plugins(self, registry: _HasPlugin) -> None:
        for stage_plugins in self.stages.values():
            for name in stage_plugins:
                if not registry.has_plugin(name):
                    available = []
                    if hasattr(registry, "list_plugins"):
                        available = registry.list_plugins()
                    raise KeyError(
                        f"Plugin '{name}' not found. Available plugins: {available}"
                    )
