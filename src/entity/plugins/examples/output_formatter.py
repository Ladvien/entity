from __future__ import annotations

from ..output_adapter import OutputAdapterPlugin


class OutputFormatter(OutputAdapterPlugin):
    """Return the final result to the user."""

    async def _execute_impl(self, context) -> str:  # noqa: D401
        message = context.message or ""
        context.say(f"Result: {message}")
        return message
