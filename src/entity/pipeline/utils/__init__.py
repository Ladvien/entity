"""Utility helpers used by the pipeline package."""

from entity.core.resources.container import DependencyGraph
from typing import Any, Iterable, List, Mapping, Type
import logging
from ..stages import PipelineStage


def _normalize_stages(stages: Any) -> List[PipelineStage]:
    """Return a list of valid ``PipelineStage`` items."""

    if isinstance(stages, Iterable) and not isinstance(stages, (str, PipelineStage)):
        return [PipelineStage.ensure(s) for s in stages]
    return [PipelineStage.ensure(stages)]


def _mro_has_class(cls: Type, name: str) -> bool:
    """Return True if ``cls`` inherits from a class with ``name``."""
    return any(base.__name__ == name for base in cls.mro()[1:])


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
    """Compatibility layer providing stage resolution helpers.

    If ``logger`` is not supplied, :meth:`_resolve_plugin_stages` uses
    ``logging.getLogger(__name__)`` so warnings are emitted by default.
    """

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

        When ``logger`` is ``None`` the method uses ``logging.getLogger(__name__)``
        so warnings are emitted even without an explicit logger.
        """
        logger = logger or logging.getLogger(__name__)

        cfg_value = config.get("stages") or config.get("stage")
        declared_value = getattr(plugin_class, "stages", None) or getattr(
            plugin_class, "stage", None
        )
        class_value = plugin_class.__dict__.get("stages") or plugin_class.__dict__.get(
            "stage"
        )
        inherited_value = None
        if class_value is None:
            inherited_value = declared_value

        if cfg_value is not None:
            stages = _normalize_stages(cfg_value)
        elif class_value is not None:
            stages = _normalize_stages(class_value)
        elif inherited_value is not None:
            stages = _normalize_stages(inherited_value)
        else:
            stages = [PipelineStage.THINK]

        if _mro_has_class(plugin_class, "InputAdapterPlugin") and stages != [
            PipelineStage.INPUT
        ]:
            if logger is not None:
                logger.warning(
                    "%s can only run in INPUT stage; ignoring configured %s",
                    plugin_class.__name__,
                    stages,
                )
            stages = [PipelineStage.INPUT]

        if _mro_has_class(plugin_class, "OutputAdapterPlugin") and stages != [
            PipelineStage.OUTPUT
        ]:
            if logger is not None:
                logger.warning(
                    "%s can only run in OUTPUT stage; ignoring configured %s",
                    plugin_class.__name__,
                    stages,
                )
            stages = [PipelineStage.OUTPUT]

        if (
            declared_value is not None
            and _normalize_stages(declared_value) != stages
            and logger is not None
        ):
            logger.warning(
                "%s resolved stages %s override class stages %s",
                plugin_class.__name__,
                stages,
                _normalize_stages(declared_value),
            )

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
