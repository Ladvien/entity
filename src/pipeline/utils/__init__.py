"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph

import logging
from typing import Any, Callable, Iterable, Mapping, Type

from entity.core.plugins import AdapterPlugin, PromptPlugin, ToolPlugin, Plugin
from ..stages import PipelineStage

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


class StageResolver:
    """Shared helpers for resolving plugin stages."""

    @staticmethod
    def _type_default_stages(plugin_cls: type[Plugin]) -> list[PipelineStage]:
        if issubclass(plugin_cls, ToolPlugin):
            return [PipelineStage.DO]
        if issubclass(plugin_cls, PromptPlugin):
            return [PipelineStage.THINK]
        if issubclass(plugin_cls, AdapterPlugin):
            return [PipelineStage.INPUT, PipelineStage.OUTPUT]
        return []

    @staticmethod
    def _resolve_plugin_stages(
        plugin_cls: type[Plugin],
        config: Mapping[str, Any],
        plugin: Plugin | None = None,
        *,
        logger: logging.Logger | None = None,
    ) -> tuple[list[PipelineStage], bool]:
        cfg_value = config.get("stages") or config.get("stage")
        attr_stages = getattr(plugin or plugin_cls, "stages", [])
        explicit_attr = (
            getattr(plugin, "_explicit_stages", False)
            if plugin is not None
            else bool(attr_stages)
        )
        type_defaults = StageResolver._type_default_stages(plugin_cls)
        if not (attr_stages or type_defaults):
            type_defaults = [PipelineStage.THINK]
        auto_inferred = (
            getattr(plugin, "_auto_inferred_stages", False)
            if plugin is not None
            else False
        )
        return resolve_stages(
            plugin_cls.__name__,
            cfg_value=cfg_value,
            attr_stages=attr_stages,
            explicit_attr=explicit_attr,
            type_defaults=type_defaults,
            ensure_stage=PipelineStage.ensure,
            logger=logger,
            auto_inferred=auto_inferred,
            error_type=SystemError,
        )


__all__ = ["DependencyGraph", "resolve_stages", "StageResolver"]
