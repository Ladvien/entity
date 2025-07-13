"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph
from typing import Any, Iterable, List, Mapping, Type
from ..stages import PipelineStage


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
        """Return stages and whether they were explicitly provided.

        Stages are resolved in the following order:
        1. ``stage``/``stages`` keys in ``config``.
        2. ``stage`` or ``stages`` attributes on ``plugin_class``.
        3. Inherited stage attributes on parent classes.
        4. Fallback to ``PipelineStage.THINK``.

        The returned ``explicit`` flag is ``True`` when a stage comes from
        configuration, the plugin instance (``_explicit_stages``), or a class
        attribute. When an instance is supplied and no explicit stage is found,
        the fallback stage is also treated as explicit.
        """
        cfg_value = config.get("stages") or config.get("stage")
        class_value = plugin_class.__dict__.get("stages") or plugin_class.__dict__.get(
            "stage"
        )
        inherited_value = None
        if class_value is None:
            inherited_value = getattr(plugin_class, "stages", None) or getattr(
                plugin_class, "stage", None
            )

        if cfg_value is not None:
            stages = _normalize_stages(cfg_value)
            if (
                class_value is not None
                and _normalize_stages(class_value) != stages
                and logger is not None
            ):
                logger.warning(
                    "%s config overrides declared stage %s -> %s",
                    plugin_class.__name__,
                    _normalize_stages(class_value),
                    stages,
                )
        elif class_value is not None:
            stages = _normalize_stages(class_value)
        elif inherited_value is not None:
            stages = _normalize_stages(inherited_value)
        else:
            stages = [PipelineStage.THINK]

        explicit_cfg = bool(cfg_value)

        explicit_instance = bool(getattr(_instance, "_explicit_stages", False))

        explicit_class = bool(class_value)

        explicit = explicit_cfg or explicit_instance or explicit_class
        if _instance is not None and not explicit:
            explicit = True

        return stages, explicit


__all__ = [
    "DependencyGraph",
    "resolve_stages",
    "get_plugin_stages",
    "StageResolver",
]
