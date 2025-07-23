from __future__ import annotations

from ..input_adapter import InputAdapterPlugin


class InputReader(InputAdapterPlugin):
    """Simple INPUT stage plugin that passes the prompt through."""

    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return the incoming message unchanged."""
        return context.message or ""
