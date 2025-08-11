from __future__ import annotations

from entity.plugins.input_adapter import InputAdapterPlugin


class InputReader(InputAdapterPlugin):
    """Simple INPUT stage plugin that passes the prompt through."""

    async def _execute_impl(self, context) -> str:
        """Store and return the incoming message."""
        message = context.message or ""
        history = await context.recall("history", [])
        history.append(message)
        await context.remember("history", history)
        await context.remember("input", message)
        return message
