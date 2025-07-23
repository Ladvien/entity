from __future__ import annotations

from ..prompt import PromptPlugin
from ...workflow.executor import WorkflowExecutor


class ReasonGenerator(PromptPlugin):
    """Generate reasoning about the extracted keywords."""

    supported_stages = [WorkflowExecutor.THINK]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        keywords = await context.recall("keywords", [])
        llm = context.get_resource("llm")
        prompt = f"Reason about: {', '.join(keywords)}"
        reasoning = (
            await llm.generate(prompt)
            if llm is not None
            else f"Reason: {', '.join(keywords)}"
        )
        await context.remember("reasoning", reasoning)
        return context.message or ""
