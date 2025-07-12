"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph
from typing import Any, Iterable, List, Mapping, Type
from pipeline.stages import PipelineStage


def _normalize_stages(stages: Any) -> List[PipelineStage]:
    """Return a list of valid ``PipelineStage`` items."""

    if isinstance(stages, Iterable) and not isinstance(stages, (str, PipelineStage)):
        return [PipelineStage.ensure(s) for s in stages]
    return [PipelineStage.ensure(stages)]


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


class StageResolver:
    """Compatibility layer providing stage resolution helpers."""

    @staticmethod
    def _resolve_plugin_stages(
        plugin_class: Type,
        config: Mapping[str, Any],
        _instance: Any | None = None,
        logger: Any | None = None,
    ) -> tuple[list[PipelineStage], bool]:
        stages = resolve_stages(plugin_class, config)
        explicit = bool(
            (config.get("stage") or config.get("stages"))
            or getattr(_instance, "_explicit_stages", False)
            or getattr(plugin_class, "stages", None)
            or getattr(plugin_class, "stage", None)
        )
        return stages, explicit


__all__ = [
    "DependencyGraph",
    "resolve_stages",
    "get_plugin_stages",
    "StageResolver",
]
