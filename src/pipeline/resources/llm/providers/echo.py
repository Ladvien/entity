from __future__ import annotations

from .base import BaseProvider


class EchoProvider(BaseProvider):
    """Adapter that simply echoes the prompt."""

    name = "echo"

    async def generate(self, prompt: str) -> str:  # noqa: D401 - simple echo
        return prompt
