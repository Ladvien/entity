from __future__ import annotations

"""Example workflow classes."""

from entity.pipeline.stages import PipelineStage

from . import Workflow


class ChainOfThoughtWorkflow(Workflow):
    """Reason through problems step by step."""

    stage_map = {PipelineStage.THINK: ["{prompt}"]}

    def __init__(
        self,
        prompt: str = "plugin_library.prompts.chain_of_thought:ChainOfThoughtPrompt",
    ) -> None:
        super().__init__(prompt=prompt)


class ReActWorkflow(Workflow):
    """Iteratively reason and act using tools."""

    stage_map = {PipelineStage.THINK: ["{prompt}"]}

    def __init__(
        self,
        prompt: str = "plugin_library.prompts.react_prompt:ReActPrompt",
    ) -> None:
        super().__init__(prompt=prompt)


class IntentClassificationWorkflow(Workflow):
    """Classify the user's intent with a single prompt."""

    stage_map = {PipelineStage.THINK: ["{prompt}"]}

    def __init__(
        self,
        prompt: str = "plugin_library.prompts.intent_classifier:IntentClassifierPrompt",
    ) -> None:
        super().__init__(prompt=prompt)


__all__ = [
    "ChainOfThoughtWorkflow",
    "ReActWorkflow",
    "IntentClassificationWorkflow",
]
