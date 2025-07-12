from __future__ import annotations

from datetime import datetime
from typing import Any

from entity.core.registries import SystemRegistries
from entity.core.state import ConversationEntry
from pipeline.pipeline import execute_pipeline
from pipeline.state import PipelineState


class PipelineWorker:
    """Stateless executor that runs a pipeline for a conversation."""

    def __init__(self, registries: SystemRegistries) -> None:
        self.registries = registries

    async def run_stages(self, state: PipelineState) -> Any:
        """Delegate pipeline execution to the existing driver."""
        # user_message is ignored when ``state`` is provided
        return await execute_pipeline("", self.registries, state=state)

    async def execute_pipeline(self, pipeline_id: str, message: str) -> Any:
        """Process ``message`` using the pipeline identified by ``pipeline_id``."""
        memory = self.registries.resources.get("memory")
        conversation = await memory.load_conversation(pipeline_id)
        conversation.append(
            ConversationEntry(content=message, role="user", timestamp=datetime.now())
        )
        state = PipelineState(conversation=conversation, pipeline_id=pipeline_id)
        result = await self.run_stages(state)
        await memory.save_conversation(pipeline_id, state.conversation)
        return result
