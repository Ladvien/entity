from __future__ import annotations

"""Utilities for combining workflows."""


from entity.pipeline.stages import PipelineStage

from .base import Workflow

__all__ = ["compose_workflows", "merge_workflows"]


def compose_workflows(*workflows: Workflow) -> Workflow:
    """Return a new workflow concatenating plugin lists per stage."""

    mapping: dict[PipelineStage, list[str]] = {}
    for wf in workflows:
        for stage, plugins in wf.stages.items():
            mapping.setdefault(stage, []).extend(list(plugins))
    wf_obj = Workflow(mapping)
    wf_obj.stage_map = mapping
    return wf_obj


def merge_workflows(*workflows: Workflow) -> Workflow:
    """Return a new workflow where later workflows override earlier ones."""

    mapping: dict[PipelineStage, list[str]] = {}
    for wf in workflows:
        for stage, plugins in wf.stages.items():
            mapping[stage] = list(plugins)
    wf_obj = Workflow(mapping)
    wf_obj.stage_map = mapping
    return wf_obj
