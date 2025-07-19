"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph
from typing import Any, Mapping, List, Type
from entity.core.stage_utils import StageResolver, _normalize_stages
from ..stages import PipelineStage


def resolve_stages(
    plugin_class: Type, config: Mapping[str, Any]
) -> List[PipelineStage]:
    """Return final stages following Decision #4."""

    cfg_value = config.get("stages") or config.get("stage")
    if cfg_value is not None:
        return _normalize_stages(cfg_value)

    class_stages = getattr(plugin_class, "stages", None) or getattr(
        plugin_class, "stage", None
    )
    if class_stages is not None:
        return _normalize_stages(class_stages)

    return [PipelineStage.THINK]


# Backward compatible alias
get_plugin_stages = resolve_stages


__all__ = [
    "DependencyGraph",
    "resolve_stages",
    "get_plugin_stages",
    "StageResolver",
]
