from __future__ import annotations

"""Built-in workflow blueprints."""

from pipeline.stages import PipelineStage

from .base import Workflow


class StandardWorkflow(Workflow):
    """Default conversational workflow."""

    def __init__(self) -> None:
        super().__init__(
            {
                PipelineStage.PARSE: ["conversation_history"],
                PipelineStage.THINK: ["complex_prompt"],
                PipelineStage.REVIEW: ["pii_scrubber"],
                PipelineStage.ERROR: ["default_responder"],
            }
        )


class ReActWorkflow(Workflow):
    """Workflow using the ReAct reasoning pattern."""

    def __init__(self) -> None:
        super().__init__(
            {
                PipelineStage.THINK: ["react"],
                PipelineStage.REVIEW: ["pii_scrubber"],
                PipelineStage.ERROR: ["default_responder"],
            }
        )


class ChainOfThoughtWorkflow(Workflow):
    """Workflow using chain-of-thought reasoning."""

    def __init__(self) -> None:
        super().__init__(
            {
                PipelineStage.THINK: ["chain_of_thought"],
                PipelineStage.REVIEW: ["pii_scrubber"],
                PipelineStage.ERROR: ["default_responder"],
            }
        )
