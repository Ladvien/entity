from __future__ import annotations

from ..base import Plugin


class InputPlugin(Plugin):
    async def run(self, message: str, user_id: str) -> str:  # noqa: D401
        """Return input unchanged."""
        return message


class ParsePlugin(Plugin):
    async def run(self, message: str, user_id: str) -> str:  # noqa: D401
        """Return message unchanged."""
        return message


class ThinkPlugin(Plugin):
    async def run(self, message: str, user_id: str) -> str:  # noqa: D401
        """Return message unchanged."""
        return message


class DoPlugin(Plugin):
    async def run(self, message: str, user_id: str) -> str:  # noqa: D401
        """Return message unchanged."""
        return message


class ReviewPlugin(Plugin):
    async def run(self, message: str, user_id: str) -> str:  # noqa: D401
        """Return message unchanged."""
        return message


class OutputPlugin(Plugin):
    async def run(self, message: str, user_id: str) -> str:  # noqa: D401
        """Return final response."""
        return message


def default_workflow() -> list[type[Plugin]]:
    """Return the built-in workflow with one plugin per stage."""

    return [
        InputPlugin,
        ParsePlugin,
        ThinkPlugin,
        DoPlugin,
        ReviewPlugin,
        OutputPlugin,
    ]
