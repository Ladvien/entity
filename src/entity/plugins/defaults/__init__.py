from __future__ import annotations

from ..base import Plugin
from ...cli.ent_cli_adapter import EntCLIAdapter


class InputPlugin(Plugin):
    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return input unchanged."""
        return context.message or ""


class ParsePlugin(Plugin):
    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class ThinkPlugin(Plugin):
    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class DoPlugin(Plugin):
    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class ReviewPlugin(Plugin):
    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return message unchanged."""
        return context.message or ""


class OutputPlugin(Plugin):
    async def _execute_impl(self, context) -> str:  # noqa: D401
        """Return final response."""
        return context.message or ""


def default_workflow() -> list[type[Plugin]]:
    """Return the built-in workflow with one plugin per stage."""

    return [
        EntCLIAdapter,
        ParsePlugin,
        ThinkPlugin,
        DoPlugin,
        ReviewPlugin,
        EntCLIAdapter,
    ]
