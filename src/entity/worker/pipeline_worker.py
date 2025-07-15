from __future__ import annotations

from datetime import datetime
from typing import Any

from entity.core.registries import SystemRegistries
from entity.core.state import ConversationEntry
from entity.pipeline.pipeline import execute_pipeline
from entity.pipeline.state import PipelineState


class PipelineWorker:
    """Stateless executor that runs a pipeline for a conversation."""

    def __init__(self, registries: SystemRegistries) -> None:
        self.registries = registries

    async def run_stages(self, state: PipelineState, user_id: str) -> Any:
        """Delegate pipeline execution to the existing driver."""
        # user_message is ignored when ``state`` is provided
        container = (
            self.registries.resources.clone()
            if hasattr(self.registries.resources, "clone")
            else self.registries.resources
        )
        regs = SystemRegistries(
            resources=container,
            tools=self.registries.tools,
            plugins=self.registries.plugins,
            validators=self.registries.validators,
        )
        return await execute_pipeline(
            "",
            regs,
            state=state,
            workflow=None,
            user_id=user_id,
        )

    async def execute_pipeline(
        self, pipeline_id: str, message: str, *, user_id: str
    ) -> Any:
        """Process ``message`` using the pipeline identified by ``pipeline_id`` and ``user_id``."""
        container = (
            self.registries.resources.clone()
            if hasattr(self.registries.resources, "clone")
            else self.registries.resources
        )
        regs = SystemRegistries(
            resources=container,
            tools=self.registries.tools,
            plugins=self.registries.plugins,
            validators=self.registries.validators,
        )

        async def _run(cont: Any) -> Any:
            memory = cont.get("memory") if hasattr(cont, "get") else cont["memory"]
            conversation = await memory.load_conversation(pipeline_id, user_id=user_id)
            conversation.append(
                ConversationEntry(
                    content=message, role="user", timestamp=datetime.now()
                )
            )
            await memory.save_conversation(pipeline_id, conversation, user_id=user_id)
            temp_key = f"{pipeline_id}_temp"
            temp_thoughts = await memory.fetch_persistent(temp_key, {}, user_id=user_id)
            state = PipelineState(
                conversation=conversation,
                temporary_thoughts=temp_thoughts,
                pipeline_id=pipeline_id,
            )
            result = await self.run_stages(state, user_id)
            await memory.save_conversation(
                pipeline_id, state.conversation, user_id=user_id
            )
            await memory.store_persistent(
                temp_key, state.temporary_thoughts, user_id=user_id
            )
            return result

        if hasattr(container, "__aenter__"):
            async with container:
                return await _run(container)
        return await _run(container)


__all__ = ["PipelineWorker"]
