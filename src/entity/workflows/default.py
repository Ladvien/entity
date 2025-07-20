from __future__ import annotations

# ruff: noqa: E402

"""Default minimal workflow."""

from entity.pipeline.stages import PipelineStage

from .base import Workflow


class DefaultWorkflow(Workflow):
    """Simple INPUT -> THINK -> OUTPUT workflow."""

    stage_map = {
        PipelineStage.INPUT: ["input_logger"],
        PipelineStage.PARSE: ["message_parser"],
        PipelineStage.THINK: [],
        PipelineStage.REVIEW: ["response_reviewer"],
        PipelineStage.OUTPUT: ["failure_responder"],
        PipelineStage.ERROR: ["basic_error_handler"],
    }


# Convenient pre-built instance for quick startup
default_workflow = DefaultWorkflow()
