from __future__ import annotations

import re
from typing import Any

from pipeline.base_plugins import PromptPlugin
from pipeline.context import PluginContext
from pipeline.stages import PipelineStage
from pipeline.state import ConversationEntry


class PIIScrubberPrompt(PromptPlugin):
    """Scrub email addresses and phone numbers from text."""

    dependencies = ["llm"]

    stages = [PipelineStage.REVIEW]

    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_PATTERN = re.compile(
        r"(?:\+?\d{1,3}[-. ]?)?(?:\(?\d{3}\)?[-. ]?)?\d{3}[-. ]?\d{4}"
    )

    async def _execute_impl(self, context: PluginContext) -> None:
        new_history = [
            self._scrub_entry(entry) for entry in context.get_conversation_history()
        ]
        context.replace_conversation_history(new_history)
        if context.has_response():
            context.update_response(self._scrub_value)

    def _scrub_entry(self, entry: ConversationEntry) -> ConversationEntry:
        """Return ``entry`` with its content sanitized."""

        entry.content = self._scrub_text(entry.content)
        return entry

    def _scrub_text(self, text: str) -> str:
        """Replace email addresses and phone numbers in ``text``."""

        text = self.EMAIL_PATTERN.sub("[email]", text)
        text = self.PHONE_PATTERN.sub("[phone]", text)
        return text

    def _scrub_value(self, value: Any) -> Any:
        """Recursively sanitize ``value`` if it contains text."""

        if isinstance(value, str):
            return self._scrub_text(value)
        if isinstance(value, dict):
            return {k: self._scrub_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._scrub_value(v) for v in value]
        return value
