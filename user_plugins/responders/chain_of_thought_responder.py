from __future__ import annotations

from typing import List

from entity.core.context import PluginContext
from entity.core.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ChainOfThoughtResponder(PromptPlugin):
    """Emit reasoning steps produced by ``ChainOfThoughtPrompt``."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        breakdown = await context.reflect("problem_breakdown", "")
        steps: List[str] = await context.reflect("reasoning_steps", [])
        final_parts: list[str] = []
        if breakdown:
            final_parts.append(f"Problem breakdown: {breakdown}")
        for idx, step in enumerate(steps, 1):
            final_parts.append(f"Step {idx}: {step}")
        await context.say("\n".join(final_parts))
