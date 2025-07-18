"""Runtime plugin validation helpers."""

from __future__ import annotations

from typing import Any, Iterable

from entity.core.stages import PipelineStage
from entity.core.stage_utils import StageResolver
from entity.utils.logging import get_logger


logger = get_logger(__name__)


def verify_stage_assignment(plugin: Any, stage: PipelineStage) -> None:
    """Ensure ``stage`` is allowed for ``plugin``."""

    stages, explicit = StageResolver._resolve_plugin_stages(
        plugin.__class__, getattr(plugin, "config", {}), plugin, logger=logger
    )
    if not explicit:
        raise ValueError(
            f"Plugin '{plugin.__class__.__name__}' must declare stages explicitly"
        )
    if stage not in stages:
        raise ValueError(
            f"Plugin '{plugin.__class__.__name__}' cannot execute in {stage}."
            f" Declared stages: {[s.name for s in stages]}"
        )


def verify_dependencies(plugin: Any, names: Iterable[str]) -> None:
    """Ensure ``plugin`` dependencies exist within ``names``."""

    plugin_name = getattr(plugin, "name", plugin.__class__.__name__)
    for dep in getattr(plugin, "dependencies", []):
        optional = str(dep).endswith("?")
        dep_name = str(dep)[:-1] if optional else str(dep)
        if dep_name == plugin_name:
            raise ValueError(f"Plugin '{plugin_name}' cannot depend on itself")
        if dep_name not in names and not optional:
            available = ", ".join(sorted(names))
            raise ValueError(
                f"Plugin '{plugin_name}' requires '{dep_name}' but it's not registered. "
                f"Available: {available}"
            )
