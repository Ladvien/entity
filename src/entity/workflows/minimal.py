from __future__ import annotations

"""Minimal workflow mapping."""

from entity.pipeline.stages import PipelineStage

from .base import Workflow


class MinimalWorkflow(Workflow):
    """Basic INPUT -> THINK -> OUTPUT flow."""

    stage_map = {
        PipelineStage.INPUT: ["input_logger"],
        PipelineStage.THINK: ["ComplexPrompt"],
        PipelineStage.OUTPUT: ["ComplexPromptResponder", "basic_error_responder"],
        PipelineStage.ERROR: ["basic_error_handler"],
    }


minimal_workflow = MinimalWorkflow()

__all__ = ["MinimalWorkflow", "minimal_workflow"]
