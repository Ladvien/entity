"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph

from typing import Any, Iterable, List, Mapping, Type

from pipeline.stages import PipelineStage


def _normalize_stages(stages: Any) -> List[PipelineStage]:
    """Return a list of valid ``PipelineStage`` items."""

    if isinstance(stages, Iterable) and not isinstance(stages, (str, PipelineStage)):
        return [PipelineStage.ensure(s) for s in stages]
    return [PipelineStage.ensure(stages)]


def get_plugin_stages(
    plugin_class: Type, config: Mapping[str, Any]
) -> List[PipelineStage]:
    """Return final stages for ``plugin_class`` following Decision #4."""

    cfg_value = config.get("stages") or config.get("stage")
    if cfg_value is not None:
        return _normalize_stages(cfg_value)

    class_stages = getattr(plugin_class, "stages", None) or getattr(
        plugin_class, "stage", None
    )
    if class_stages is not None:
        return _normalize_stages(class_stages)

    return [PipelineStage.THINK]


__all__ = ["DependencyGraph", "get_plugin_stages"]
