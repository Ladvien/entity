from __future__ import annotations

from typing import Any, Dict, cast

from .manager import PipelineManager
from .execution import execute_pipeline
from .registries import SystemRegistries


class ConversationManager:
    """Coordinate multi-turn processing through repeated pipeline execution."""

    def __init__(
        self,
        registries: SystemRegistries,
        pipeline_manager: PipelineManager | None = None,
    ) -> None:
        self._registries = registries
        self._pipeline_manager = pipeline_manager or PipelineManager(registries)

    async def process_request(self, user_message: str) -> Dict[str, Any]:
        """Process a user message, delegating back to the pipeline when needed."""
        response = cast(
            Dict[str, Any],
            await execute_pipeline(
                user_message,
                self._registries,
                pipeline_manager=self._pipeline_manager,
            ),
        )
        while (
            isinstance(response, dict) and response.get("type") == "continue_processing"
        ):
            follow_up = str(response.get("message", ""))
            response = cast(
                Dict[str, Any],
                await execute_pipeline(
                    follow_up,
                    self._registries,
                    pipeline_manager=self._pipeline_manager,
                ),
            )
        return response
