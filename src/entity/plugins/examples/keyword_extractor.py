from __future__ import annotations

import re
from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class KeywordExtractor(Plugin):
    """Extract lowercase keywords from the prompt and store them."""

    supported_stages = [WorkflowExecutor.PARSE]

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Persist keywords and return the original message."""
        text = await context.recall("input", context.message or "")
        keywords = list(dict.fromkeys(re.findall(r"\w+", text.lower())))
        await context.remember("keywords", keywords)
        return text
