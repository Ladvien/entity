class DependencyGraph:
    def __init__(self, graph):
        self.graph = graph

    def topological_sort(self):  # pragma: no cover - simple stub
        return list(self.graph)


import logging
from typing import Any, Callable, Iterable, Type


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


__all__ = ["DependencyGraph", "resolve_stages"]
