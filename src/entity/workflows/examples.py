from __future__ import annotations

"""Example workflow classes."""

from pipeline.stages import PipelineStage

from . import Workflow


class ChainOfThoughtWorkflow(Workflow):
    """Reason through problems step by step."""

    stage_map = {
        PipelineStage.THINK: [
            "user_plugins.prompts.chain_of_thought:ChainOfThoughtPrompt",
        ]
    }


class ReActWorkflow(Workflow):
    """Iteratively reason and act using tools."""

    stage_map = {
        PipelineStage.THINK: [
            "user_plugins.prompts.react_prompt:ReActPrompt",
        ]
    }


class IntentClassificationWorkflow(Workflow):
    """Classify the user's intent with a single prompt."""

    stage_map = {
        PipelineStage.THINK: [
            "user_plugins.prompts.intent_classifier:IntentClassifierPrompt",
        ]
    }


__all__ = [
    "ChainOfThoughtWorkflow",
    "ReActWorkflow",
    "IntentClassificationWorkflow",
]
