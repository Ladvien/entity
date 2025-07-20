from __future__ import annotations

"""Built-in workflow blueprints."""

from entity.pipeline.stages import PipelineStage

from .base import Workflow


class StandardWorkflow(Workflow):
    """Default conversational workflow."""

    stage_map = {
        PipelineStage.PARSE: ["conversation_history"],
        PipelineStage.THINK: ["complex_prompt"],
        PipelineStage.REVIEW: ["pii_scrubber"],
        PipelineStage.OUTPUT: ["failure_responder"],
        PipelineStage.ERROR: ["default_responder"],
    }


class ReActWorkflow(Workflow):
    """Workflow using the ReAct reasoning pattern."""

    stage_map = {
        PipelineStage.THINK: ["react"],
        PipelineStage.REVIEW: ["pii_scrubber"],
        PipelineStage.OUTPUT: ["failure_responder"],
        PipelineStage.ERROR: ["default_responder"],
    }


class ChainOfThoughtWorkflow(Workflow):
    """Workflow using chain-of-thought reasoning."""

    stage_map = {
        PipelineStage.THINK: ["chain_of_thought"],
        PipelineStage.REVIEW: ["pii_scrubber"],
        PipelineStage.OUTPUT: ["failure_responder"],
        PipelineStage.ERROR: ["default_responder"],
    }
