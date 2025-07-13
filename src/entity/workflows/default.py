from __future__ import annotations

# ruff: noqa: E402

"""Default minimal workflow."""

from entity.pipeline.stages import PipelineStage

from .base import Workflow


class DefaultWorkflow(Workflow):
    """Simple INPUT -> THINK -> OUTPUT workflow."""

    stage_map = {
        PipelineStage.INPUT: [],
        PipelineStage.THINK: [],
        PipelineStage.OUTPUT: [],
    }


# Convenient pre-built instance for quick startup
default_workflow = DefaultWorkflow()
