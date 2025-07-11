from __future__ import annotations

"""Stateless pipeline worker.

Loads conversation context from memory for each request and
persists updates after execution.
"""

from datetime import datetime
from typing import Any

from entity.core.registries import SystemRegistries
from entity.core.state import ConversationEntry

from .pipeline import execute_pipeline
from .state import PipelineState


class PipelineWorker:
    """Execute pipelines without retaining local state."""

    def __init__(self, registries: SystemRegistries) -> None:
        self.registries = registries

    async def run_stages(self, state: PipelineState) -> Any:
        """Return the assistant response for the provided state."""
        return state.conversation[-1].content

    async def execute_pipeline(self, pipeline_id: str, message: str) -> Any:
        """Process ``message`` for ``pipeline_id``."""
        memory = self.registries.resources.get("memory")
        history = await memory.load_conversation(pipeline_id)
        history.append(
            ConversationEntry(content=message, role="user", timestamp=datetime.now())
        )
        state = PipelineState(conversation=history, pipeline_id=pipeline_id)
        result = await self.run_stages(state)
        await memory.save_conversation(pipeline_id, state.conversation)
        return result


__all__ = ["PipelineWorker"]
