"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph

import logging
from typing import Any, Callable, Iterable, Mapping, Type

from entity.core.plugins import AdapterPlugin, PromptPlugin, ToolPlugin, Plugin
from ..stages import PipelineStage


def resolve_stages(
    name: str,
    *,
    cfg_value: Any | None,
    attr_stages: Iterable[Any],
    explicit_attr: bool,
    type_defaults: Iterable[Any],
    ensure_stage: Callable[[Any], Any],
    logger: logging.Logger | None = None,
    auto_inferred: bool = False,
    error_type: Type[Exception] = SystemError,
) -> tuple[list[Any], bool]:
    """Resolve final stages and whether they were explicit."""

    logger = logger or logging.getLogger(__name__)
    attr_stages = [ensure_stage(s) for s in attr_stages]
    type_defaults = [ensure_stage(s) for s in type_defaults]
    stages: list[Any] = []
    explicit = False
    source = None

    if cfg_value is not None:
        stages = cfg_value if isinstance(cfg_value, list) else [cfg_value]
        stages = [ensure_stage(s) for s in stages]
        explicit = True
        source = "config"
        if explicit_attr and set(stages) != set(attr_stages):
            logger.warning(
                "Plugin '%s' config stages %s override class stages %s",
                name,
                [str(s) for s in stages],
                [str(s) for s in attr_stages],
            )
    elif explicit_attr:
        stages = attr_stages
        explicit = True
        source = "class"
    elif type_defaults:
        stages = type_defaults
    elif auto_inferred:
        stages = attr_stages

    if not stages:
        stages = attr_stages or type_defaults

    if explicit and type_defaults and set(stages) != set(type_defaults):
        logger.warning(
            "Plugin '%s' explicit %s stages %s override type defaults %s",
            name,
            source or "config",
            [str(s) for s in stages],
            [str(s) for s in type_defaults],
        )

    if not stages:
        raise error_type(f"No stage specified for {name}")

    return stages, explicit


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
