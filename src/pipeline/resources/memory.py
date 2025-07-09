"""Pipeline memory resource wrappers."""

from __future__ import annotations

from entity.resources.memory import Memory as _Memory
from pipeline.pipeline import execute_pipeline
from entity.core.registries import SystemRegistries


class Conversation:
    """Simple conversation helper for tests."""

    def __init__(self, capabilities: SystemRegistries) -> None:
        self._caps = capabilities

    async def process_request(self, message: str):
        result = await execute_pipeline(message, self._caps)
        while isinstance(result, dict) and result.get("type") == "continue_processing":
            next_msg = result.get("message", "")
            result = await execute_pipeline(next_msg, self._caps)
        return result


class Memory(_Memory):
    """Expose start_conversation on top of base Memory."""

    dependencies: list[str] = []

    def start_conversation(
        self, capabilities: SystemRegistries, _manager: object | None = None
    ) -> Conversation:
        return Conversation(capabilities)
