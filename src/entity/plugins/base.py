from __future__ import annotations


class Plugin:
    """Minimal plugin interface used in tests."""

    def __init__(self, resources: dict[str, object]):
        self.resources = resources

    async def run(self, message: str, user_id: str) -> str:
        return message
