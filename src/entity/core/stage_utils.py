from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Type

from .stages import PipelineStage


def _normalize_stages(stages: Any) -> List[PipelineStage]:
    """Return a list of valid ``PipelineStage`` items."""
    if isinstance(stages, Iterable) and not isinstance(stages, (str, PipelineStage)):
        return [PipelineStage.ensure(s) for s in stages]
    return [PipelineStage.ensure(stages)]


class StageResolver:
    """Helpers to resolve and validate plugin stages."""

    @staticmethod
    def _resolve_plugin_stages(
        plugin_class: Type,
        config: Mapping[str, Any],
        _instance: Any | None = None,
        logger: Any | None = None,
    ) -> tuple[list[PipelineStage], bool]:
        """Return stages and whether they were explicit."""
        logger = logger
        cfg_value = config.get("stages") or config.get("stage")
        declared_value = getattr(plugin_class, "stages", None) or getattr(
            plugin_class, "stage", None
        )
        if (
            cfg_value is not None
            and declared_value is not None
            and _normalize_stages(cfg_value) != _normalize_stages(declared_value)
            and logger is not None
        ):
            logger.warning(
                "%s configuration stages %s override declared stages %s",
                plugin_class.__name__,
                _normalize_stages(cfg_value),
                _normalize_stages(declared_value),
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

        if (
            hasattr(plugin_class, "InputAdapterPlugin")
            and any(
                base.__name__ == "InputAdapterPlugin" for base in plugin_class.mro()[1:]
            )
            and stages != [PipelineStage.INPUT]
        ):
            if logger is not None:
                logger.warning(
                    "%s can only run in INPUT stage; ignoring configured %s",
                    plugin_class.__name__,
                    stages,
                )
            stages = [PipelineStage.INPUT]

        if (
            hasattr(plugin_class, "OutputAdapterPlugin")
            and any(
                base.__name__ == "OutputAdapterPlugin"
                for base in plugin_class.mro()[1:]
            )
            and stages != [PipelineStage.OUTPUT]
        ):
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

        return stages, explicit


__all__ = ["_normalize_stages", "StageResolver"]
